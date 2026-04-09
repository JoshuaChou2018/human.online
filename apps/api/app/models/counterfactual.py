"""
反事实模拟（Counterfactual Simulation）数据模型
用于模拟假设性事件在数字社会中的传播和演变
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class ScenarioType(str, PyEnum):
    """场景类型"""
    POLITICAL = "political"          # 政治事件
    ECONOMIC = "economic"            # 经济事件
    SOCIAL = "social"                # 社会事件
    TECHNOLOGY = "technology"        # 科技事件
    ENVIRONMENT = "environment"      # 环境事件
    CUSTOM = "custom"                # 自定义


class SimulationPhase(str, PyEnum):
    """模拟阶段"""
    INITIAL = "initial"              # 初始反应
    SPREAD = "spread"                # 传播扩散
    DEBATE = "debate"                # 观点辩论
    EVOLUTION = "evolution"          # 话题演变
    CONSENSUS = "consensus"          # 趋于共识/极化


class CounterfactualScenario(Base):
    """反事实场景定义"""
    __tablename__ = "counterfactual_scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 场景基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    scenario_type = Column(Enum(ScenarioType), default=ScenarioType.CUSTOM)
    
    # 触发事件（新闻、声明等）
    trigger_event = Column(Text, nullable=False)
    trigger_source = Column(String(100))  # 事件来源（如：特朗普、白宫、新华社）
    
    # 模拟参数
    max_rounds = Column(Integer, default=5)  # 最大轮数
    avatar_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    
    # 初始情绪设定
    initial_sentiment = Column(Float, default=0.0)  # -1 到 1
    initial_heat = Column(Float, default=0.5)       # 0 到 1，热度
    
    # 状态
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    
    # 结果摘要
    final_summary = Column(Text)
    key_findings = Column(JSON, default=list)  # 关键发现
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("User")
    rounds = relationship("SimulationRound", back_populates="scenario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CounterfactualScenario(id={self.id}, title={self.title})>"


class SimulationRound(Base):
    """模拟轮次（每轮代表一个时间节点）"""
    __tablename__ = "simulation_rounds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("counterfactual_scenarios.id"), nullable=False)
    round_number = Column(Integer, nullable=False)  # 第几轮
    
    # 阶段
    phase = Column(Enum(SimulationPhase), default=SimulationPhase.INITIAL)
    
    # 本轮话题
    topic = Column(String(200))           # 当前讨论话题
    topic_keywords = Column(JSON, default=list)  # 关键词
    
    # 舆论指标
    sentiment_score = Column(Float, default=0.0)      # 情绪分数
    sentiment_distribution = Column(JSON, default=dict)  # 情绪分布
    stance_distribution = Column(JSON, default=dict)    # 立场分布（支持/反对/中立）
    heat_score = Column(Float, default=0.0)           # 热度
    polarization_index = Column(Float, default=0.0)   # 极化指数
    
    # 传播指标
    reach_count = Column(Integer, default=0)          # 影响人数
    message_count = Column(Integer, default=0)        # 消息数量
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    scenario = relationship("CounterfactualScenario", back_populates="rounds")
    responses = relationship("AgentResponse", back_populates="round", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SimulationRound(scenario={self.scenario_id}, round={self.round_number})>"


class ResponseType(str, PyEnum):
    """反应类型"""
    INITIAL_REACTION = "initial_reaction"    # 初始反应
    REPLY = "reply"                          # 回复他人
    AMPLIFY = "amplify"                      # 放大传播
    REFUTE = "refute"                        # 反驳
    QUESTION = "question"                    # 质疑
    JOKE = "joke"                            # 调侃/讽刺
    ANALYSIS = "analysis"                    # 深度分析
    EMOTIONAL = "emotional"                  # 情绪宣泄


class AgentResponse(Base):
    """分身（Agent）在模拟中的反应/发言"""
    __tablename__ = "agent_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id = Column(UUID(as_uuid=True), ForeignKey("simulation_rounds.id"), nullable=False)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    
    # 如果是回复，记录父消息
    parent_response_id = Column(UUID(as_uuid=True), ForeignKey("agent_responses.id"), nullable=True)
    
    # 反应内容
    content = Column(Text, nullable=False)        # 发言内容
    response_type = Column(Enum(ResponseType), default=ResponseType.INITIAL_REACTION)
    
    # 情绪与立场
    sentiment = Column(Float, default=0.0)        # 情绪值
    stance = Column(String(20), default="neutral")  # 立场：support, oppose, neutral
    confidence = Column(Float, default=0.5)       # 置信度
    
    # 思维过程（LLM的思考过程）
    thinking_process = Column(Text)               # 为什么这样反应
    personality_factors = Column(JSON, default=dict)  # 哪些性格因素影响了反应
    
    # 传播指标
    influence_score = Column(Float, default=0.0)  # 影响力分数
    reply_count = Column(Integer, default=0)      # 被回复次数
    spread_count = Column(Integer, default=0)     # 被转发/引用次数
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    round = relationship("SimulationRound", back_populates="responses")
    avatar = relationship("Avatar")
    parent = relationship("AgentResponse", remote_side=[id])
    
    def __repr__(self):
        return f"<AgentResponse(avatar={self.avatar_id}, round={self.round_id})>"


class TopicEvolution(Base):
    """话题演变追踪"""
    __tablename__ = "topic_evolutions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("counterfactual_scenarios.id"), nullable=False)
    
    # 话题信息
    topic_name = Column(String(200), nullable=False)
    keywords = Column(JSON, default=list)
    
    # 演变过程
    evolution_path = Column(JSON, default=list)   # [{round: 1, sentiment: 0.2}, ...]
    
    # 热度变化
    heat_timeline = Column(JSON, default=list)    # 热度时间线
    
    # 关键参与者
    key_supporters = Column(JSON, default=list)   # 主要支持者
    key_opponents = Column(JSON, default=list)    # 主要反对者
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TopicEvolution(scenario={self.scenario_id}, topic={self.topic_name})>"
