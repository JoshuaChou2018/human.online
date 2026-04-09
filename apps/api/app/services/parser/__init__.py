"""
数据解析服务
"""
from typing import Dict, Any
from uuid import UUID
from app.core.config import settings
from app.models.avatar import DataSourceType, DataSourceStatus


async def parse_data_source(source_id: str, file_path: str, source_type: DataSourceType):
    """
    启动数据源解析任务
    
    这里应该使用 Celery 进行异步处理，简化版本直接调用
    """
    from app.services.parser.tasks import process_data_source
    
    # 异步处理
    import asyncio
    asyncio.create_task(process_data_source(source_id, file_path, source_type))
    
    return {"task": "started", "source_id": source_id}
