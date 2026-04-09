"""
文件存储服务
"""
import os
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from uuid import uuid4
from app.core.config import settings


async def save_upload_file(upload_file: UploadFile) -> str:
    """保存上传的文件到本地存储"""
    
    # 检查文件大小
    contents = await upload_file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # 重置文件指针
    await upload_file.seek(0)
    
    # 创建存储目录
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = Path(upload_file.filename).suffix
    unique_filename = f"{uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # 保存文件
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    return str(file_path)


async def read_file_content(file_path: str) -> str:
    """读取文件内容"""
    path = Path(file_path)
    
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    # 根据文件类型选择读取方式
    ext = path.suffix.lower()
    
    if ext in ['.txt', '.md', '.csv', '.json']:
        # 文本文件
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return await f.read()
    
    elif ext in ['.pdf']:
        # PDF 文件 - 使用解析器处理
        from app.services.parser.parsers import parse_pdf
        return await parse_pdf(file_path)
    
    elif ext in ['.docx', '.doc']:
        # Word 文档
        from app.services.parser.parsers import parse_docx
        return await parse_docx(file_path)
    
    else:
        # 尝试作为文本读取
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return await f.read()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}"
            )


def delete_file(file_path: str) -> bool:
    """删除文件"""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False
