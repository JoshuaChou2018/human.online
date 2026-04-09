"""
沙盒观察者 API
获取沙盒中的 psyche 成员和实时活动
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.auth import get_current_user, get_optional_user
from app.models.user import User
from app.models.avatar import Avatar, AvatarStatus
from app.models.simulation import SandboxMember
from app.models.conversation import Message, Conversation

router = APIRouter(prefix="/sandbox", tags=["沙盒"])


class SandboxMemberResponse(BaseModel):
    id: str
    avatar_id: str
    name: str
    status: str
    avatar_url: Optional[str]
    color: str
    last_activity_at: Optional[str]
    total_messages: int
    current_topic: Optional[str]
    is_in_sandbox: bool  # 是否实际在沙盒中（有SandboxMember记录）


class SandboxActivityResponse(BaseModel):
    id: str
    name: str
    avatar: str
    action: str
    message: Optional[str]
    emotion: str
    topic: Optional[str]
    timestamp: str


class SandboxStatsResponse(BaseModel):
    total_members: int
    active_members: int
    total_messages: int
    hot_topics: List[dict]


class ToggleSandboxRequest(BaseModel):
    avatar_id: str
    join: bool  # True = 加入沙盒, False = 离开沙盒


def generate_color(name: str) -> str:
    """基于名称生成颜色"""
    colors = [
        "from-gray-700 to-gray-900",
        "from-blue-500 to-indigo-600",
        "from-red-500 to-orange-600",
        "from-green-500 to-teal-600",
        "from-amber-500 to-orange-600",
        "from-purple-500 to-pink-600",
        "from-cyan-500 to-blue-600",
        "from-rose-500 to-pink-600",
    ]
    return colors[hash(name) % len(colors)]


@router.get("/members", response_model=List[SandboxMemberResponse])
async def get_sandbox_members(
    only_active: bool = False,  # 如果为True，只返回实际在沙盒中的
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取沙盒中的所有 psyche 成员
    返回所有公开且就绪的分身（分身池），标记哪些实际在沙盒中
    """
    # 查询所有公开且就绪的分身（分身池）
    result = await db.execute(
        select(Avatar)
        .where(
            and_(
                Avatar.is_public == True,
                Avatar.status == AvatarStatus.READY
            )
        )
        .order_by(desc(Avatar.updated_at))
    )
    
    avatars = result.scalars().all()
    
    # 查询哪些分身有沙盒成员记录
    sandbox_result = await db.execute(
        select(SandboxMember)
        .where(SandboxMember.status == "active")
    )
    sandbox_members = {str(m.avatar_id): m for m in sandbox_result.scalars().all()}
    
    members = []
    for avatar in avatars:
        member = sandbox_members.get(str(avatar.id))
        
        # 如果要求只返回活跃沙盒成员，且这个avatar不在沙盒中，跳过
        if only_active and not member:
            continue
        
        members.append(SandboxMemberResponse(
            id=str(member.id) if member else str(avatar.id),
            avatar_id=str(avatar.id),
            name=avatar.name,
            status=member.status if member else "inactive",
            avatar_url=None,
            color=generate_color(avatar.name),
            last_activity_at=member.last_activity_at.isoformat() if member and member.last_activity_at else avatar.updated_at.isoformat(),
            total_messages=member.total_messages if member else 0,
            current_topic=member.current_topic if member else None,
            is_in_sandbox=member is not None,
        ))
    
    return members


@router.post("/toggle", response_model=dict)
async def toggle_sandbox_member(
    request: ToggleSandboxRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    将分身加入或移出沙盒
    - 只能操作自己的分身
    - 分身必须是公开的且状态为 READY
    """
    # 验证分身所有权
    result = await db.execute(
        select(Avatar).where(
            Avatar.id == UUID(request.avatar_id),
            Avatar.user_id == current_user.id
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found or not owned by you"
        )
    
    if not avatar.is_public:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only public avatars can join sandbox"
        )
    
    if avatar.status != AvatarStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar must be ready to join sandbox"
        )
    
    if request.join:
        # 加入沙盒
        result = await db.execute(
            select(SandboxMember).where(SandboxMember.avatar_id == UUID(request.avatar_id))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.status = "active"
            existing.last_activity_at = datetime.utcnow()
        else:
            member = SandboxMember(
                avatar_id=UUID(request.avatar_id),
                user_id=current_user.id,
                status="active",
                last_activity_at=datetime.utcnow(),
            )
            db.add(member)
        
        avatar.sandbox_status = "active"
        message = f"{avatar.name} 已加入沙盒"
    else:
        # 离开沙盒
        result = await db.execute(
            select(SandboxMember).where(SandboxMember.avatar_id == UUID(request.avatar_id))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.status = "inactive"
        
        avatar.sandbox_status = "inactive"
        message = f"{avatar.name} 已离开沙盒"
    
    await db.commit()
    
    return {"message": message, "avatar_id": request.avatar_id, "in_sandbox": request.join}


@router.get("/activities", response_model=List[SandboxActivityResponse])
async def get_sandbox_activities(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取沙盒实时活动流（从真实消息中获取）"""
    # 获取最近的消息作为活动
    result = await db.execute(
        select(Message, Avatar)
        .join(Avatar, Message.sender_id == Avatar.id)
        .where(
            Avatar.is_public == True,
            Avatar.status == AvatarStatus.READY
        )
        .order_by(desc(Message.created_at))
        .limit(limit)
    )
    
    activities = []
    messages = result.all()
    
    for msg, avatar in messages:
        # 从消息元数据判断是否是 AI 消息
        is_ai = (msg.message_metadata or {}).get("is_ai", False)
        
        # 根据情绪状态确定 emotion
        emotion = "neutral"
        if msg.emotion_state:
            pleasure = msg.emotion_state.get("pleasure", 0)
            if pleasure > 0.3:
                emotion = "positive"
            elif pleasure < -0.3:
                emotion = "negative"
            elif msg.emotion_state.get("arousal", 0) > 0.5:
                emotion = "excited"
        
        # AI 消息是 speaking，用户消息是 reacting
        action = "speaking" if is_ai else "reacting"
        
        activities.append(SandboxActivityResponse(
            id=str(msg.id),
            name=avatar.name,
            avatar=avatar.name[0].upper(),
            action=action,
            message=msg.content[:200] if msg.content else None,  # 限制长度
            emotion=emotion,
            topic=None,
            timestamp=msg.created_at.isoformat() if msg.created_at else datetime.utcnow().isoformat(),
        ))
    
    # 如果没有真实消息，返回空列表
    return activities


@router.get("/stats", response_model=SandboxStatsResponse)
async def get_sandbox_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取沙盒统计信息"""
    # 实际在沙盒中的成员数
    active_result = await db.execute(
        select(func.count(SandboxMember.id)).where(SandboxMember.status == "active")
    )
    active_members = active_result.scalar()
    
    # 分身池总数（公开且就绪）
    total_result = await db.execute(
        select(func.count(Avatar.id)).where(
            and_(Avatar.is_public == True, Avatar.status == AvatarStatus.READY)
        )
    )
    total_members = total_result.scalar()
    
    # 总消息数
    messages_result = await db.execute(
        select(func.sum(SandboxMember.total_messages))
    )
    total_messages = messages_result.scalar() or 0
    
    # 热门话题（从沙盒成员的 current_topic 统计）
    from collections import Counter
    
    # 获取所有活跃成员的当前话题
    topics_result = await db.execute(
        select(SandboxMember.current_topic, SandboxMember.current_emotion)
        .where(
            and_(
                SandboxMember.status == "active",
                SandboxMember.current_topic.isnot(None)
            )
        )
    )
    topic_data = topics_result.all()
    
    # 统计话题出现频率
    topic_counts = Counter([t[0] for t in topic_data if t[0]])
    total_active = max(active_members, 1)
    
    # 构建热门话题列表
    hot_topics = []
    for topic, count in topic_counts.most_common(5):
        # 计算情感倾向
        emotions = [t[1] for t in topic_data if t[0] == topic and t[1]]
        sentiment = "neutral"
        if emotions:
            # 简单判断情感倾向
            positive_count = sum(1 for e in emotions if e and isinstance(e, dict) and e.get('pleasure', 0) > 0.3)
            negative_count = sum(1 for e in emotions if e and isinstance(e, dict) and e.get('pleasure', 0) < -0.3)
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
        
        # 热度根据参与者比例计算
        heat = min(100, int((count / total_active) * 100) + 20)
        
        hot_topics.append({
            "topic": topic,
            "heat": heat,
            "participants": count,
            "sentiment": sentiment
        })
    
    # 如果没有话题，返回空列表
    if not hot_topics:
        hot_topics = []
    
    return SandboxStatsResponse(
        total_members=total_members,
        active_members=active_members,
        total_messages=total_messages,
        hot_topics=hot_topics,
    )


@router.get("/pool", response_model=List[dict])
async def get_avatar_pool(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取分身池 - 所有公开且就绪的分身
    用于手动选择哪些分身加入沙盒
    """
    result = await db.execute(
        select(Avatar)
        .where(
            and_(
                Avatar.is_public == True,
                Avatar.status == AvatarStatus.READY
            )
        )
        .order_by(desc(Avatar.updated_at))
    )
    
    avatars = result.scalars().all()
    
    # 查询哪些在沙盒中
    sandbox_result = await db.execute(
        select(SandboxMember).where(SandboxMember.status == "active")
    )
    in_sandbox = {str(m.avatar_id) for m in sandbox_result.scalars().all()}
    
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "description": a.description,
            "user_id": str(a.user_id),
            "is_in_sandbox": str(a.id) in in_sandbox,
            "color": generate_color(a.name),
            "avatar_type": a.avatar_type.value if a.avatar_type else "personal",
        }
        for a in avatars
    ]
