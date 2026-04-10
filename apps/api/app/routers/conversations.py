"""
对话相关路由
支持多 LLM 提供商
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.avatar import Avatar
from app.models.conversation import Conversation, Message, ConversationType
from app.schemas.avatar import ChatMessageRequest, ChatMessageResponse
from app.services.chat import generate_avatar_response
from pydantic import BaseModel

router = APIRouter(prefix="/conversations", tags=["对话"])


class CreateConversationRequest(BaseModel):
    participant_ids: List[UUID]
    title: Optional[str] = None


@router.post("", response_model=dict)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新对话"""
    participant_ids = list(request.participant_ids)  # 复制列表
    title = request.title
    
    # 验证所有参与者是否存在
    for avatar_id in participant_ids:
        result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Avatar {avatar_id} not found"
            )
        
        # 检查权限
        if not avatar.is_public and avatar.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to chat with avatar {avatar_id}"
            )
    
    # 获取用户的个人分身并添加到参与者列表
    user_avatar_result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.user_id == current_user.id,
                Avatar.avatar_type == "personal"
            )
        ).limit(1)
    )
    user_avatar = user_avatar_result.scalar_one_or_none()
    
    if user_avatar and user_avatar.id not in participant_ids:
        participant_ids.append(user_avatar.id)
    
    # 确定对话类型
    conv_type = ConversationType.GROUP if len(participant_ids) > 1 else ConversationType.PRIVATE
    
    conversation = Conversation(
        type=conv_type,
        title=title or ("Group Chat" if conv_type == ConversationType.GROUP else "Private Chat"),
        participant_ids=participant_ids,
        creator_id=current_user.id
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "type": conversation.type,
        "title": conversation.title,
        "participant_ids": conversation.participant_ids,
        "created_at": conversation.created_at
    }


@router.get("", response_model=List[dict])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的对话列表"""
    from sqlalchemy.orm import selectinload
    
    # 预加载 messages 避免幼载加载问题
    result = await db.execute(
        select(Conversation)
        .where(Conversation.creator_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .options(selectinload(Conversation.messages))
    )
    
    conversations = result.scalars().all()
    
    # 获取参与者信息
    result_list = []
    for conv in conversations:
        # 获取参与者详情
        participants = []
        for avatar_id in conv.participant_ids:
            avatar_result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
            avatar = avatar_result.scalar_one_or_none()
            if avatar:
                participants.append({
                    "id": avatar.id,
                    "name": avatar.name,
                    "avatar_type": avatar.avatar_type,
                    "description": avatar.description
                })
        
        # 获取最后一条消息
        last_message = None
        if conv.messages:
            last_msg = conv.messages[-1]
            last_message = {
                "id": last_msg.id,
                "content": last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content,
                "created_at": last_msg.created_at
            }
        
        result_list.append({
            "id": conv.id,
            "type": conv.type,
            "title": conv.title,
            "participants": participants,
            "last_message": last_message,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at
        })
    
    return result_list


@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话详情"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # 获取参与者信息
    participants = []
    for avatar_id in conversation.participant_ids:
        avatar_result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
        avatar = avatar_result.scalar_one_or_none()
        if avatar:
            participants.append({
                "id": avatar.id,
                "name": avatar.name,
                "description": avatar.description,
                "avatar_type": avatar.avatar_type
            })
    
    return {
        "id": conversation.id,
        "type": conversation.type,
        "title": conversation.title,
        "participants": participants,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at
    }


@router.get("/{conversation_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = 50,
    before_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话消息"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    query = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).limit(limit)
    
    if before_id:
        query = query.where(Message.id < before_id)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # 获取用户的个人分身ID
    user_avatar_result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.user_id == current_user.id,
                Avatar.avatar_type == "personal"
            )
        ).limit(1)
    )
    user_avatar = user_avatar_result.scalar_one_or_none()
    user_avatar_id = user_avatar.id if user_avatar else None
    
    # 构建响应
    response = []
    for msg in reversed(messages):  # 返回时间正序
        sender_result = await db.execute(
            select(Avatar).where(Avatar.id == msg.sender_id)
        )
        sender = sender_result.scalar_one_or_none()
        
        # 判断是否是 AI 消息（优先检查 metadata）
        is_ai_message = msg.message_metadata and msg.message_metadata.get("is_ai", False)
        
        # 判断是否是当前用户发送的消息（优先检查 metadata 中的 is_user 标记）
        is_user_message = msg.message_metadata and msg.message_metadata.get("is_user", False)
        
        # 如果没有明确标记，使用旧逻辑：不是 AI 消息且 sender_id 匹配用户的 personal 分身
        if not is_user_message and not is_ai_message:
            is_user_message = bool(user_avatar_id and msg.sender_id == user_avatar_id)
        
        if is_user_message:
            sender_name = "You"
        elif is_ai_message and sender:
            sender_name = sender.name  # AI 消息显示分身名称
        elif sender:
            sender_name = sender.name
        else:
            sender_name = "Unknown"
        
        response.append(ChatMessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            sender_name=sender_name,
            content=msg.content,
            is_user=is_user_message,
            emotion_state=msg.emotion_state,
            created_at=msg.created_at
        ))
    
    return response


@router.post("/{conversation_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    conversation_id: UUID,
    data: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息并获取 AI 响应
    
    可选指定 LLM 提供商:
    - provider: openai | kimi | anthropic
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # 创建用户消息（使用用户的个人分身作为发送者）
    user_avatar_result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.user_id == current_user.id,
                Avatar.avatar_type == "personal"
            )
        ).limit(1)
    )
    user_avatar = user_avatar_result.scalar_one_or_none()
    
    if not user_avatar:
        # 如果没有个人分身，使用第一个参与者
        user_avatar_id = conversation.participant_ids[0]
    else:
        user_avatar_id = user_avatar.id
    
    # 保存用户消息（标记 is_user 以便区分）
    user_message = Message(
        conversation_id=conversation_id,
        sender_id=user_avatar_id,
        content=data.content,
        message_metadata={"is_user": True}
    )
    db.add(user_message)
    conversation.message_count += 1
    await db.commit()
    await db.refresh(user_message)
    
    # 生成 AI 响应（每个非用户参与者都回复）
    ai_responses = []
    provider_used = None
    
    # 确定哪些分身需要回复（排除用户分身，但如果只有用户分身则使用它）
    ai_avatar_ids = [aid for aid in conversation.participant_ids if aid != user_avatar_id]
    
    # 如果只有用户分身（没有独立的AI分身），则用户分身也作为AI回复
    if not ai_avatar_ids and conversation.participant_ids:
        ai_avatar_ids = conversation.participant_ids
    
    for avatar_id in ai_avatar_ids:
        # 获取分身信息
        avatar_result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
        avatar = avatar_result.scalar_one_or_none()
        
        if not avatar:
            continue
        
        # 生成响应，传入 provider 参数
        try:
            response_content, emotion = await generate_avatar_response(
                avatar=avatar,
                conversation=conversation,
                user_message=data.content,
                db=db,
                provider=data.provider
            )
            
            # 记录使用的提供商
            if not provider_used and avatar.cognitive_config:
                provider_used = avatar.cognitive_config.get("provider_used")
            
        except Exception as e:
            print(f"[Chat] Error generating response from {avatar.name}: {e}")
            response_content = f"抱歉，我暂时无法回应。"
            emotion = None
        
        # 保存 AI 消息
        ai_message = Message(
            conversation_id=conversation_id,
            sender_id=avatar_id,
            content=response_content,
            emotion_state=emotion,
            message_metadata={"is_ai": True}
        )
        db.add(ai_message)
        conversation.message_count += 1
        await db.commit()
        await db.refresh(ai_message)
        
        ai_responses.append(ChatMessageResponse(
            id=ai_message.id,
            conversation_id=ai_message.conversation_id,
            sender_id=ai_message.sender_id,
            sender_name=avatar.name,
            content=ai_message.content,
            is_user=False,  # AI 消息
            emotion_state=ai_message.emotion_state,
            provider_used=provider_used,
            created_at=ai_message.created_at
        ))
    
    # 返回最后一条 AI 响应（简化处理）
    if ai_responses:
        return ai_responses[0]
    
    return ChatMessageResponse(
        id=user_message.id,
        conversation_id=user_message.conversation_id,
        sender_id=user_message.sender_id,
        sender_name="You",
        content=user_message.content,
        is_user=True,  # 用户消息
        created_at=user_message.created_at
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    硬删除对话及其所有消息
    """
    # 查询对话
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # 验证权限（只有创建者可以删除）
    if conversation.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this conversation"
        )
    
    # 硬删除所有关联消息
    await db.execute(
        Message.__table__.delete().where(Message.conversation_id == conversation_id)
    )
    
    # 删除对话
    await db.delete(conversation)
    await db.commit()
    
    return None
