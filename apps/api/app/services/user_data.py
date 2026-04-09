"""
用户数据管理服务
处理用户数据源的存储、查询、删除等
"""
import uuid
import os
import shutil
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status, UploadFile

from app.core.config import settings
from app.models.user import User, UserDataSource
from app.services.parser.parsers import parse_file


# 确保上传目录存在
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def get_user_data_sources(user: User, db: AsyncSession) -> List[UserDataSource]:
    """获取用户的所有数据源"""
    result = await db.execute(
        select(UserDataSource).where(
            UserDataSource.user_id == user.id
        ).order_by(UserDataSource.created_at.desc())
    )
    return result.scalars().all()


async def get_data_source(
    data_source_id: str,
    user: User,
    db: AsyncSession
) -> Optional[UserDataSource]:
    """获取单个数据源详情"""
    result = await db.execute(
        select(UserDataSource).where(
            UserDataSource.id == uuid.UUID(data_source_id),
            UserDataSource.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def upload_data_source(
    user: User,
    file: UploadFile,
    name: Optional[str],
    description: Optional[str],
    source_type: str,
    db: AsyncSession
) -> UserDataSource:
    """
    上传并保存用户数据源
    1. 保存文件到存储
    2. 解析文件内容
    3. 创建数据源记录
    """
    # 生成唯一文件名
    file_ext = Path(file.filename or "unknown").suffix
    unique_filename = f"{user.id}_{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    
    # 解析文件内容
    processing_result = {}
    try:
        parsed_content = parse_file(str(file_path), file.content_type or "application/octet-stream")
        processing_result = {
            "parsed": True,
            "content_preview": parsed_content[:1000] if isinstance(parsed_content, str) else str(parsed_content)[:1000],
            "content_length": len(parsed_content) if isinstance(parsed_content, str) else len(str(parsed_content)),
        }
        status = "completed"
    except Exception as e:
        processing_result = {
            "parsed": False,
            "error": str(e),
        }
        status = "failed"
    
    # 创建数据源记录
    data_source = UserDataSource(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name or file.filename or "Untitled",
        description=description,
        source_type=source_type,
        file_name=file.filename or "unknown",
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        status=status,
        processing_result=processing_result,
    )
    db.add(data_source)
    await db.commit()
    await db.refresh(data_source)
    
    return data_source


async def delete_data_source(
    data_source_id: str,
    user: User,
    db: AsyncSession
) -> bool:
    """
    删除用户数据源
    1. 检查是否被 avatar 使用
    2. 删除关联的 data_sources 记录
    3. 删除文件
    4. 删除数据库记录
    """
    from app.models.avatar import DataSource
    
    result = await db.execute(
        select(UserDataSource).where(
            UserDataSource.id == uuid.UUID(data_source_id),
            UserDataSource.user_id == user.id
        )
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        return False
    
    # 检查是否被使用（关联到 avatar）
    if data_source.use_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete: this data source is used by {data_source.use_count} avatar(s)"
        )
    
    # 先删除关联的 data_sources 记录（外键约束）
    await db.execute(
        delete(DataSource).where(DataSource.user_data_source_id == uuid.UUID(data_source_id))
    )
    
    # 删除文件
    if data_source.file_path and os.path.exists(data_source.file_path):
        try:
            os.remove(data_source.file_path)
        except Exception:
            pass  # 文件可能已被删除
    
    # 删除数据库记录
    await db.delete(data_source)
    await db.commit()
    
    return True


async def update_data_source(
    data_source_id: str,
    user: User,
    name: Optional[str],
    description: Optional[str],
    db: AsyncSession
) -> Optional[UserDataSource]:
    """更新数据源信息"""
    result = await db.execute(
        select(UserDataSource).where(
            UserDataSource.id == uuid.UUID(data_source_id),
            UserDataSource.user_id == user.id
        )
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        return None
    
    if name is not None:
        data_source.name = name
    if description is not None:
        data_source.description = description
    
    data_source.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(data_source)
    
    return data_source


async def get_data_source_content(
    data_source_id: str,
    user: User,
    db: AsyncSession
) -> Optional[str]:
    """获取数据源的解析后内容"""
    data_source = await get_data_source(data_source_id, user, db)
    
    if not data_source:
        return None
    
    # 从 processing_result 获取内容预览
    if data_source.processing_result and "content_preview" in data_source.processing_result:
        return data_source.processing_result["content_preview"]
    
    # 如果文件存在，重新解析
    if data_source.file_path and os.path.exists(data_source.file_path):
        try:
            content = parse_file(data_source.file_path, data_source.mime_type or "application/octet-stream")
            return content[:5000]  # 限制返回长度
        except Exception:
            pass
    
    return None
