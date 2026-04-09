"""
数据源相关路由
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.avatar import Avatar, DataSource, DataSourceStatus, DataSourceType
from app.schemas.avatar import DataSourceResponse
from app.services.storage import save_upload_file
from app.services.parser import parse_data_source

router = APIRouter(prefix="/avatars/{avatar_id}/data-sources", tags=["数据源"])


@router.get("", response_model=List[DataSourceResponse])
async def list_data_sources(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据源列表"""
    # 检查权限
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    if avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    result = await db.execute(
        select(DataSource).where(DataSource.avatar_id == avatar_id)
        .order_by(DataSource.created_at.desc())
    )
    
    return result.scalars().all()


@router.post("", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def upload_data_source(
    avatar_id: UUID,
    source_type: DataSourceType = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传数据源文件"""
    # 检查权限
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    if avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # 保存文件
    file_path = await save_upload_file(file)
    
    # 创建数据源记录
    data_source = DataSource(
        avatar_id=avatar_id,
        source_type=source_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=0,  # 会在解析时更新
        mime_type=file.content_type,
        status=DataSourceStatus.PENDING
    )
    
    db.add(data_source)
    await db.commit()
    await db.refresh(data_source)
    
    # 启动解析任务
    await parse_data_source(str(data_source.id), file_path, source_type)
    
    return data_source


@router.get("/{source_id}", response_model=DataSourceResponse)
async def get_data_source(
    avatar_id: UUID,
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个数据源详情"""
    result = await db.execute(
        select(DataSource).where(
            and_(
                DataSource.id == source_id,
                DataSource.avatar_id == avatar_id
            )
        )
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # 检查权限
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return data_source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    avatar_id: UUID,
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据源"""
    result = await db.execute(
        select(DataSource).where(
            and_(
                DataSource.id == source_id,
                DataSource.avatar_id == avatar_id
            )
        )
    )
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # 检查权限
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    await db.delete(data_source)
    await db.commit()
    
    return None
