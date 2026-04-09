"""
数字分身服务
处理 psyche 创建、沙盒加入、重建等功能
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.user import User, UserDataSource
from app.models.avatar import Avatar, DataSource, AvatarStatus, AvatarType
from app.models.simulation import SandboxMember
from app.schemas.avatar import AvatarCreate, AvatarResponse
from app.services.mindweave_analyzer import analyze_mindweave_features, generate_identity_card


async def create_avatar_for_user(
    user: User,
    name: str,
    description: Optional[str],
    data_source_ids: List[str],
    is_public: bool,
    db: AsyncSession
) -> Avatar:
    """
    为用户创建数字分身
    1. 检查用户免费额度
    2. 创建 avatar
    3. 关联数据源
    4. 如果是公开分身，自动加入沙盒
    """
    # 检查免费额度
    if not user.can_create_free_avatar:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free avatar quota exceeded. Please upgrade your plan."
        )
    
    # 验证数据源所有权
    data_source_uuids = [uuid.UUID(ds_id) for ds_id in data_source_ids]
    result = await db.execute(
        select(UserDataSource).where(
            UserDataSource.id.in_(data_source_uuids),
            UserDataSource.user_id == user.id
        )
    )
    user_data_sources = result.scalars().all()
    
    if len(user_data_sources) != len(data_source_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some data sources not found or not owned by user"
        )
    
    # 创建 avatar
    avatar = Avatar(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name,
        description=description,
        avatar_type=AvatarType.PERSONAL,
        status=AvatarStatus.WEAVING,  # 设为编织中，等待 MindWeave 分析完成
        is_public=is_public,
        auto_join_sandbox=is_public,
        sandbox_status="inactive",  # 先不加入沙盒，等编织完成
        used_data_source_ids=[str(ds_id) for ds_id in data_source_ids],
    )
    db.add(avatar)
    
    # 创建关联的 DataSource 记录
    data_source_objects = []
    for ds in user_data_sources:
        data_source = DataSource(
            id=uuid.uuid4(),
            avatar_id=avatar.id,
            user_data_source_id=ds.id,
            source_type=ds.source_type,
            file_name=ds.file_name,
            file_path=ds.file_path,
            file_size=ds.file_size,
            mime_type=ds.mime_type,
            status="completed",  # 用户数据源已处理完成
        )
        db.add(data_source)
        data_source_objects.append(data_source)
    
    # 更新用户已创建数量
    user.avatars_created += 1
    
    await db.flush()
    await db.commit()
    await db.refresh(avatar)
    
    # 启动 MindWeave 编织任务（使用新的进度追踪）
    from app.services.mindweave.weaving import start_weaving_task
    asyncio.create_task(start_weaving_task(
        str(avatar.id),
        [str(ds.id) for ds in data_source_objects],
        provider=None
    ))
    
    return avatar


async def _analyze_avatar_mindweave(avatar_id: uuid.UUID, db: AsyncSession):
    """异步分析分身的 MindWeave 特征"""
    try:
        # 重新查询 avatar（因为原来的 session 可能已关闭）
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as new_db:
            result = await new_db.execute(
                select(Avatar).where(Avatar.id == avatar_id)
            )
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                return
            
            # 进行 MindWeave 分析
            mind_profile = await analyze_mindweave_features(avatar, new_db)
            
            # 生成身份卡
            identity_card = await generate_identity_card(avatar, mind_profile)
            
            # 保存到 avatar
            avatar.mind_weave_profile = {
                "mindThreads": mind_profile,
                "identityCard": identity_card,
                "analyzedAt": datetime.utcnow().isoformat()
            }
            
            await new_db.commit()
            print(f"Avatar {avatar_id} MindWeave analysis completed")
            
    except Exception as e:
        print(f"MindWeave analysis failed for avatar {avatar_id}: {e}")
        import traceback
        traceback.print_exc()


async def add_avatar_to_sandbox(avatar: Avatar, db: AsyncSession) -> SandboxMember:
    """将 psyche 加入沙盒"""
    # 检查是否已经在沙盒中
    result = await db.execute(
        select(SandboxMember).where(SandboxMember.avatar_id == avatar.id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # 更新状态
        existing.status = "active"
        existing.last_activity_at = datetime.utcnow()
        await db.commit()
        return existing
    
    # 创建新的沙盒成员
    member = SandboxMember(
        id=uuid.uuid4(),
        avatar_id=avatar.id,
        user_id=avatar.user_id,
        status="active",
        last_activity_at=datetime.utcnow(),
    )
    db.add(member)
    
    # 更新 avatar 的沙盒状态
    avatar.sandbox_status = "active"
    avatar.last_sandbox_activity = datetime.utcnow()
    
    await db.commit()
    await db.refresh(member)
    
    return member


async def remove_avatar_from_sandbox(avatar_id: str, db: AsyncSession) -> bool:
    """将 psyche 从沙盒中移除"""
    result = await db.execute(
        select(SandboxMember).where(SandboxMember.avatar_id == uuid.UUID(avatar_id))
    )
    member = result.scalar_one_or_none()
    
    if member:
        member.status = "inactive"
        await db.commit()
        
        # 更新 avatar 状态
        result = await db.execute(
            select(Avatar).where(Avatar.id == uuid.UUID(avatar_id))
        )
        avatar = result.scalar_one_or_none()
        if avatar:
            avatar.sandbox_status = "inactive"
            await db.commit()
        
        return True
    
    return False


async def rebuild_avatar(
    avatar_id: str,
    user: User,
    data_source_ids: Optional[List[str]],
    db: AsyncSession
) -> Avatar:
    """
    重建数字分身
    1. 验证用户所有权
    2. 如果有新数据源，替换数据源
    3. 重置状态为 weaving
    4. 重新加入沙盒（如果之前不在）
    """
    result = await db.execute(
        select(Avatar).where(
            Avatar.id == uuid.UUID(avatar_id),
            Avatar.user_id == user.id
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 如果有新数据源，验证并更新
    if data_source_ids is not None:
        data_source_uuids = [uuid.UUID(ds_id) for ds_id in data_source_ids]
        result = await db.execute(
            select(UserDataSource).where(
                UserDataSource.id.in_(data_source_uuids),
                UserDataSource.user_id == user.id
            )
        )
        user_data_sources = result.scalars().all()
        
        if len(user_data_sources) != len(data_source_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some data sources not found or not owned by user"
            )
        
        # 删除旧的 DataSource 记录
        await db.execute(
            update(DataSource).where(
                DataSource.avatar_id == avatar.id
            ).values(status="archived")
        )
        
        # 创建新的 DataSource 记录
        for ds in user_data_sources:
            data_source = DataSource(
                id=uuid.uuid4(),
                avatar_id=avatar.id,
                user_data_source_id=ds.id,
                source_type=ds.source_type,
                file_name=ds.file_name,
                file_path=ds.file_path,
                file_size=ds.file_size,
                mime_type=ds.mime_type,
                status="pending",
            )
            db.add(data_source)
        
        avatar.used_data_source_ids = [str(ds_id) for ds_id in data_source_ids]
    
    # 重置状态为 weaving
    avatar.status = AvatarStatus.WEAVING
    avatar.updated_at = datetime.utcnow()
    
    # 确保在沙盒中
    if avatar.sandbox_status != "active":
        await add_avatar_to_sandbox(avatar, db)
    
    await db.commit()
    await db.refresh(avatar)
    
    return avatar


async def get_user_avatars(user: User, db: AsyncSession) -> List[Avatar]:
    """获取用户的所有 psyche"""
    result = await db.execute(
        select(Avatar).where(
            Avatar.user_id == user.id,
            Avatar.status != "archived"
        ).order_by(Avatar.created_at.desc())
    )
    return result.scalars().all()


async def delete_avatar(avatar_id: str, user: User, db: AsyncSession) -> bool:
    """删除 psyche（从数据库中永久删除）
    
    需要先删除所有关联数据（按正确顺序）：
    1. 消息表
    2. 模拟事件
    3. 模拟结果
    4. 社交关系
    5. 沙盒成员
    6. 数据源
    7. 最后删除分身
    """
    from app.models.simulation import SandboxMember, SimulationEvent, SocialRelation, Simulation
    from app.models.conversation import Message, Conversation
    
    result = await db.execute(
        select(Avatar).where(
            Avatar.id == uuid.UUID(avatar_id),
            Avatar.user_id == user.id
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        return False
    
    avatar_uuid = uuid.UUID(avatar_id)
    
    try:
        # 1. 删除该分身发起的所有模拟（级联删除 SimulationEvent）
        await db.execute(
            Simulation.__table__.delete().where(
                Simulation.initiator_avatar_id == avatar_uuid
            )
        )
        
        # 2. 删除模拟事件（作为接收者）
        await db.execute(
            SimulationEvent.__table__.delete().where(
                SimulationEvent.to_avatar_id == avatar_uuid
            )
        )
        
        # 3. 删除社交关系
        await db.execute(
            SocialRelation.__table__.delete().where(
                (SocialRelation.from_avatar_id == avatar_uuid) |
                (SocialRelation.to_avatar_id == avatar_uuid)
            )
        )
        
        # 4. 删除沙盒成员记录
        await db.execute(
            SandboxMember.__table__.delete().where(
                SandboxMember.avatar_id == avatar_uuid
            )
        )
        
        # 5. 删除该分身发送的所有消息
        await db.execute(
            Message.__table__.delete().where(
                Message.sender_id == avatar_uuid
            )
        )
        
        # 6. 删除数据源
        await db.execute(
            DataSource.__table__.delete().where(
                DataSource.avatar_id == avatar_uuid
            )
        )
        
        # 7. 最后删除分身
        await db.delete(avatar)
        
        # 8. 恢复用户免费额度
        if user.avatars_created > 0:
            user.avatars_created -= 1
        
        await db.commit()
        return True
        
    except Exception as e:
        await db.rollback()
        print(f"Delete avatar error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return True
