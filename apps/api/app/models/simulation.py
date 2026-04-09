"""
社会模拟模型
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class SimulationStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Simulation(Base):
    __tablename__ = "simulations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 创建者
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 初始消息
    initial_message = Column(Text, nullable=False)
    initiator_avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    
    # 参与的分身
    avatar_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    
    # 模拟参数
    max_steps = Column(Integer, default=10)  # 最大传播步数
    
    # 状态
    status = Column(Enum(SimulationStatus), default=SimulationStatus.PENDING)
    
    # 结果
    result = Column(JSON, default=dict)
    visualization = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("User")
    initiator = relationship("Avatar")
    events = relationship("SimulationEvent", back_populates="simulation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Simulation(id={self.id}, name={self.name}, status={self.status})>"


class ReactionType(str, PyEnum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    AMPLIFY = "amplify"
    QUESTION = "question"
    IGNORE = "ignore"


class SimulationEvent(Base):
    __tablename__ = "simulation_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False)
    
    # 传播步骤
    step = Column(Integer, nullable=False)
    
    # 传播关系
    from_avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    to_avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    
    # 反应
    reaction_type = Column(Enum(ReactionType), nullable=False)
    reaction_content = Column(Text, nullable=True)
    
    # 传播概率
    influence_probability = Column(Float, default=0.0)
    
    # 情绪状态变化
    emotion_before = Column(JSON, nullable=True)
    emotion_after = Column(JSON, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    simulation = relationship("Simulation", back_populates="events")
    from_avatar = relationship("Avatar", foreign_keys=[from_avatar_id])
    to_avatar = relationship("Avatar", foreign_keys=[to_avatar_id])
    
    def __repr__(self):
        return f"<SimulationEvent(step={self.step}, from={self.from_avatar_id}, to={self.to_avatar_id})>"


class SocialRelation(Base):
    """社交关系模型"""
    __tablename__ = "social_relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    from_avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    to_avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    
    relation_type = Column(String(20), default="follow")  # follow, friend, colleague, rival, mentor
    strength = Column(Float, default=0.5)  # 0-1
    
    interaction_history = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SocialRelation(from={self.from_avatar_id}, to={self.to_avatar_id}, type={self.relation_type})>"


class SandboxMember(Base):
    """
    沙盒成员 - 追踪哪些 psyche 在沙盒中活跃
    """
    __tablename__ = "sandbox_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # 用户创建的 psyche
    
    # 状态
    status = Column(String(20), default="active")  # active, inactive, suspended
    
    # 活动统计
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    total_messages = Column(Integer, default=0)
    total_interactions = Column(Integer, default=0)
    
    # 当前状态
    current_emotion = Column(JSON, default=dict)  # 当前情绪状态
    current_topic = Column(String(200), nullable=True)  # 当前关注的话题
    
    # 加入时间
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    avatar = relationship("Avatar")
    user = relationship("User")
    
    def __repr__(self):
        return f"<SandboxMember(avatar_id={self.avatar_id}, status={self.status})>"
