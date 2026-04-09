"""
对话和消息模型
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConversationType(str, PyEnum):
    PRIVATE = "private"
    GROUP = "group"
    SIMULATION = "simulation"


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(ConversationType), default=ConversationType.PRIVATE)
    title = Column(String(200), nullable=True)
    
    # 参与者 ID 列表
    participant_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    
    # 创建者
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 会话上下文（用于记忆）
    context = Column(JSON, default=dict)
    
    # 统计
    message_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, type={self.type})>"


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    
    # 内容
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text, image, file
    
    # 情绪状态（发送时的情绪）
    emotion_state = Column(JSON, nullable=True)  # {pleasure, arousal, dominance}
    
    # 引用的记忆向量 ID
    memory_refs = Column(ARRAY(String), default=list)
    
    # 元数据
    message_metadata = Column("metadata", JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("Avatar")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender_id})>"
