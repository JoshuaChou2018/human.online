"""
用户数据源管理路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.services.user_data import (
    get_user_data_sources, get_data_source, upload_data_source,
    delete_data_source, update_data_source, get_data_source_content
)

router = APIRouter(prefix="/user/data", tags=["用户数据管理"])


class DataSourceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    source_type: str
    file_name: str
    file_size: int
    mime_type: Optional[str]
    status: str
    use_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class DataSourceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("", response_model=List[DataSourceResponse])
async def list_my_data_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有数据源"""
    data_sources = await get_user_data_sources(current_user, db)
    return [
        DataSourceResponse(
            id=str(ds.id),
            name=ds.name,
            description=ds.description,
            source_type=ds.source_type,
            file_name=ds.file_name,
            file_size=ds.file_size,
            mime_type=ds.mime_type,
            status=ds.status,
            use_count=ds.use_count,
            created_at=ds.created_at.isoformat(),
            updated_at=ds.updated_at.isoformat(),
        )
        for ds in data_sources
    ]


@router.post("/upload", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def upload_new_data_source(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    source_type: str = Form("document"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传新的数据源"""
    data_source = await upload_data_source(
        user=current_user,
        file=file,
        name=name,
        description=description,
        source_type=source_type,
        db=db
    )
    
    return DataSourceResponse(
        id=str(data_source.id),
        name=data_source.name,
        description=data_source.description,
        source_type=data_source.source_type,
        file_name=data_source.file_name,
        file_size=data_source.file_size,
        mime_type=data_source.mime_type,
        status=data_source.status,
        use_count=data_source.use_count,
        created_at=data_source.created_at.isoformat(),
        updated_at=data_source.updated_at.isoformat(),
    )


@router.get("/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source_detail(
    data_source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个数据源详情"""
    data_source = await get_data_source(data_source_id, current_user, db)
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    return DataSourceResponse(
        id=str(data_source.id),
        name=data_source.name,
        description=data_source.description,
        source_type=data_source.source_type,
        file_name=data_source.file_name,
        file_size=data_source.file_size,
        mime_type=data_source.mime_type,
        status=data_source.status,
        use_count=data_source.use_count,
        created_at=data_source.created_at.isoformat(),
        updated_at=data_source.updated_at.isoformat(),
    )


@router.get("/{data_source_id}/content")
async def get_data_source_content_endpoint(
    data_source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据源的解析后内容预览"""
    content = await get_data_source_content(data_source_id, current_user, db)
    
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found or content not available"
        )
    
    return {"content": content}


@router.put("/{data_source_id}", response_model=DataSourceResponse)
async def update_data_source_endpoint(
    data_source_id: str,
    request: DataSourceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据源信息"""
    data_source = await update_data_source(
        data_source_id, current_user, request.name, request.description, db
    )
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    return DataSourceResponse(
        id=str(data_source.id),
        name=data_source.name,
        description=data_source.description,
        source_type=data_source.source_type,
        file_name=data_source.file_name,
        file_size=data_source.file_size,
        mime_type=data_source.mime_type,
        status=data_source.status,
        use_count=data_source.use_count,
        created_at=data_source.created_at.isoformat(),
        updated_at=data_source.updated_at.isoformat(),
    )


@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source_endpoint(
    data_source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据源"""
    success = await delete_data_source(data_source_id, current_user, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    return None
