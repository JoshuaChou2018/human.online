"""
数据解析任务
"""
import json
from typing import Dict, Any
from app.core.database import AsyncSessionLocal
from app.models.avatar import DataSource, DataSourceStatus, DataSourceType
from app.services.parser.parsers import (
    parse_chat_records,
    parse_document,
    parse_social_media,
    parse_audio_transcript
)
from sqlalchemy import select


async def process_data_source(source_id: str, file_path: str, source_type: DataSourceType):
    """处理数据源的主任务"""
    
    async with AsyncSessionLocal() as db:
        try:
            # 更新状态为处理中
            result = await db.execute(
                select(DataSource).where(DataSource.id == source_id)
            )
            data_source = result.scalar_one_or_none()
            
            if not data_source:
                print(f"DataSource {source_id} not found")
                return
            
            data_source.status = DataSourceStatus.PROCESSING
            data_source.processing_progress = 10.0
            await db.commit()
            
            # 根据类型解析
            extracted_data = {}
            
            if source_type == DataSourceType.CHAT:
                extracted_data = await parse_chat_records(file_path)
            
            elif source_type == DataSourceType.DOCUMENT:
                extracted_data = await parse_document(file_path)
            
            elif source_type == DataSourceType.SOCIAL:
                extracted_data = await parse_social_media(file_path)
            
            elif source_type == DataSourceType.AUDIO:
                extracted_data = await parse_audio_transcript(file_path)
            
            # 更新进度
            data_source.processing_progress = 80.0
            await db.commit()
            
            # 提取认知特征（简化版本）
            insights = extract_cognitive_insights(extracted_data, source_type)
            
            # 更新数据源记录
            data_source.status = DataSourceStatus.COMPLETED
            data_source.processing_progress = 100.0
            data_source.extracted_insights = insights
            data_source.metadata = {
                "extracted_stats": {
                    "total_length": len(extracted_data.get("content", "")),
                    "segments_count": len(extracted_data.get("segments", [])),
                }
            }
            await db.commit()
            
            print(f"DataSource {source_id} processed successfully")
            
        except Exception as e:
            # 更新为失败状态
            result = await db.execute(
                select(DataSource).where(DataSource.id == source_id)
            )
            data_source = result.scalar_one_or_none()
            
            if data_source:
                data_source.status = DataSourceStatus.FAILED
                data_source.error_message = str(e)
                await db.commit()
            
            print(f"Error processing DataSource {source_id}: {e}")


def extract_cognitive_insights(extracted_data: Dict[str, Any], source_type: DataSourceType) -> Dict[str, Any]:
    """从提取的数据中提取认知特征（简化版本）"""
    
    content = extracted_data.get("content", "")
    segments = extracted_data.get("segments", [])
    
    insights = {
        "source_type": source_type.value,
        "total_segments": len(segments),
        "avg_segment_length": len(content) / max(len(segments), 1),
        "key_phrases": [],  # 可以在这里提取关键词
        "topics": [],  # 可以在这里提取主题
        "sentiment_samples": [],  # 可以在这里分析情感样本
    }
    
    # 简单统计
    if content:
        # 词汇多样性
        words = content.split()
        unique_words = set(words)
        insights["vocabulary_diversity"] = len(unique_words) / max(len(words), 1)
        
        # 句子平均长度
        sentences = content.split("。")
        avg_sentence_length = sum(len(s) for s in sentences) / max(len(sentences), 1)
        insights["avg_sentence_length"] = avg_sentence_length
    
    return insights
