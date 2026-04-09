"""
用户模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # 邮箱登录用户的密码
    
    # 用户资料
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    profile = Column(JSON, default=dict)
    
    # 免费额度
    free_avatar_quota = Column(Integer, default=1)
    avatars_created = Column(Integer, default=0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # 关系
    avatars = relationship("Avatar", back_populates="owner", cascade="all, delete-orphan")
    data_sources = relationship("UserDataSource", back_populates="user", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def can_create_free_avatar(self) -> bool:
        return self.avatars_created < self.free_avatar_quota
    
    @property
    def remaining_free_quota(self) -> int:
        return max(0, self.free_avatar_quota - self.avatars_created)


class UserDataSource(Base):
    __tablename__ = "user_data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    source_type = Column(String(50), nullable=False)
    
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)
    
    content_storage_key = Column(String(255), nullable=True)
    
    # 提取的内容
    extracted_content = Column(Text, nullable=True)
    
    status = Column(String(20), default="pending")
    processing_result = Column(JSON, default=dict)
    
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    used_by_avatar_ids = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="data_sources")
    
    def __repr__(self):
        return f"<UserDataSource(id={self.id}, name={self.name}, type={self.source_type})>"
