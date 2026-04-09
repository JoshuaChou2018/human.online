"""
数字分身模型
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Text, JSON, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class AvatarType(str, PyEnum):
    PERSONAL = "personal"
    CELEBRITY = "celebrity"
    SYSTEM = "system"


class AvatarStatus(str, PyEnum):
    DRAFT = "draft"
    WEAVING = "weaving"  # 思维编织中
    READY = "ready"
    ARCHIVED = "archived"


class Avatar(Base):
    __tablename__ = "avatars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for system avatars
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 类型和状态
    avatar_type = Column(Enum(AvatarType), default=AvatarType.PERSONAL)
    status = Column(Enum(AvatarStatus), default=AvatarStatus.DRAFT)
    
    # 认知配置
    system_prompt = Column(Text, nullable=True)
    cognitive_config = Column(JSON, default=dict)  # 心智模型、决策启发式等
    style_config = Column(JSON, default=dict)  # temperature, top_p 等
    
    # 表达特征
    expression_dna = Column(JSON, default=dict)  # 语气、词汇、句式等
    
    # MindWeave 六维特征
    mind_weave_profile = Column(JSON, default=dict)  # {mindThreads, identityCard, analyzedAt}
    
    # 隐私信息（仅创建者可见）
    private_profile = Column(JSON, default=dict)  # {偏好、背景、敏感信息等}
    
    # 统计数据
    interaction_count = Column(Integer, default=0)
    knowledge_chunks_count = Column(Integer, default=0)
    
    # 向量存储 ID（用于 RAG）
    vector_collection_id = Column(String(100), nullable=True)
    
    # 公开访问
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # 沙盒自动加入
    auto_join_sandbox = Column(Boolean, default=True)  # 创建后是否自动加入沙盒
    sandbox_status = Column(String(20), default="inactive")  # inactive, active, paused
    last_sandbox_activity = Column(DateTime, nullable=True)
    
    # 使用的数据源
    used_data_source_ids = Column(JSON, default=list)  # UserDataSource IDs used for this avatar
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系 - 使用字符串引用避免循环导入
    owner = relationship("User", back_populates="avatars")
    data_sources = relationship("DataSource", back_populates="avatar", cascade="all, delete-orphan")
    weaving_progress = relationship("WeavingProgress", back_populates="avatar", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Avatar(id={self.id}, name={self.name}, type={self.avatar_type})>"


class DataSourceType(str, PyEnum):
    CHAT = "chat"
    DOCUMENT = "document"
    SOCIAL = "social"
    AUDIO = "audio"


class DataSourceStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    user_data_source_id = Column(UUID(as_uuid=True), ForeignKey("user_data_sources.id"), nullable=True)
    source_type = Column(Enum(DataSourceType), nullable=False)
    
    # 文件信息
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)
    
    # 处理状态
    status = Column(Enum(DataSourceStatus), default=DataSourceStatus.PENDING)
    processing_progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # 提取的元数据
    source_metadata = Column(JSON, default=dict)
    extracted_insights = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    avatar = relationship("Avatar", back_populates="data_sources")
    
    def __repr__(self):
        return f"<DataSource(id={self.id}, type={self.source_type}, status={self.status})>"
