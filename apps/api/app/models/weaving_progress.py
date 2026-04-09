"""
编织进度追踪模型
用于实时追踪 MindWeave 思维编织过程的进度和日志
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class WeavingStage(str, PyEnum):
    """编织阶段"""
    PREPARING = "preparing"              # 准备阶段：读取数据源
    EXTRACTING_TEXT = "extracting_text"  # 提取文本内容
    ANALYZING_MIND_CORE = "analyzing_mind_core"           # 分析思维内核
    ANALYZING_EXPRESSION = "analyzing_expression"         # 分析表达风格
    ANALYZING_DECISION = "analyzing_decision"             # 分析决策逻辑
    ANALYZING_KNOWLEDGE = "analyzing_knowledge"           # 分析知识领域
    ANALYZING_VALUES = "analyzing_values"                 # 分析价值体系
    ANALYZING_EMOTION = "analyzing_emotion"               # 分析情感模式
    WEAVING_MIND = "weaving_mind"        # 编织思维内核
    GENERATING_IDENTITY = "generating_identity"  # 生成身份卡
    COMPLETED = "completed"              # 完成
    FAILED = "failed"                    # 失败


class WeavingProgress(Base):
    """编织进度记录"""
    __tablename__ = "weaving_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False, unique=True)
    
    # 当前阶段
    current_stage = Column(Enum(WeavingStage), default=WeavingStage.PREPARING)
    
    # 总体进度 (0-100)
    overall_progress = Column(Float, default=0.0)
    
    # 各阶段进度详情
    stage_progress = Column(JSON, default=dict)  # {stage: {progress: 0-100, status: "running|completed|failed"}}
    
    # 实时日志（按时间顺序）
    logs = Column(JSON, default=list)  # [{timestamp, stage, message, type: "info|success|warning|error"}]
    
    # 当前正在分析的内容预览
    current_text_preview = Column(Text, nullable=True)
    
    # 已提取的中间结果
    intermediate_results = Column(JSON, default=dict)  # {stage: result_data}
    
    # LLM 调用统计
    llm_stats = Column(JSON, default=dict)  # {calls_count, tokens_used, provider, model}
    
    # 开始和结束时间
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    avatar = relationship("Avatar", back_populates="weaving_progress")
    
    def __repr__(self):
        return f"<WeavingProgress(avatar={self.avatar_id}, stage={self.current_stage}, progress={self.overall_progress}%)>"
    
    def add_log(self, stage: WeavingStage, message: str, log_type: str = "info", metadata: dict = None):
        """添加日志记录"""
        if self.logs is None:
            self.logs = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": stage.value if isinstance(stage, WeavingStage) else stage,
            "message": message,
            "type": log_type,
            "metadata": metadata or {}
        }
        self.logs.append(log_entry)
        
        # 限制日志数量，防止过大
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]
    
    def update_stage_progress(self, stage: WeavingStage, progress: float, status: str = "running"):
        """更新阶段进度"""
        if self.stage_progress is None:
            self.stage_progress = {}
        
        stage_key = stage.value if isinstance(stage, WeavingStage) else stage
        self.stage_progress[stage_key] = {
            "progress": progress,
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # 计算总体进度
        self._calculate_overall_progress()
    
    def _calculate_overall_progress(self):
        """计算总体进度"""
        stage_weights = {
            WeavingStage.PREPARING.value: 5,
            WeavingStage.EXTRACTING_TEXT.value: 10,
            WeavingStage.ANALYZING_MIND_CORE.value: 15,
            WeavingStage.ANALYZING_EXPRESSION.value: 15,
            WeavingStage.ANALYZING_DECISION.value: 10,
            WeavingStage.ANALYZING_KNOWLEDGE.value: 10,
            WeavingStage.ANALYZING_VALUES.value: 10,
            WeavingStage.ANALYZING_EMOTION.value: 10,
            WeavingStage.WEAVING_MIND.value: 10,
            WeavingStage.GENERATING_IDENTITY.value: 5,
        }
        
        total_weight = sum(stage_weights.values())
        weighted_progress = 0
        
        for stage_key, weight in stage_weights.items():
            stage_data = self.stage_progress.get(stage_key, {})
            if stage_data.get("status") == "completed":
                weighted_progress += weight
            else:
                weighted_progress += weight * (stage_data.get("progress", 0) / 100)
        
        self.overall_progress = round((weighted_progress / total_weight) * 100, 1)
    
    def set_intermediate_result(self, stage: WeavingStage, result: dict):
        """设置中间结果"""
        if self.intermediate_results is None:
            self.intermediate_results = {}
        
        stage_key = stage.value if isinstance(stage, WeavingStage) else stage
        self.intermediate_results[stage_key] = {
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def to_dict(self) -> dict:
        """转换为字典格式（用于 API 响应）"""
        return {
            "id": str(self.id),
            "avatar_id": str(self.avatar_id),
            "current_stage": self.current_stage.value if self.current_stage else None,
            "current_stage_label": self._get_stage_label(),
            "overall_progress": self.overall_progress,
            "stage_progress": self.stage_progress,
            "logs": self.logs or [],
            "current_text_preview": self.current_text_preview,
            "intermediate_results": self.intermediate_results,
            "llm_stats": self.llm_stats,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_running": self.current_stage not in [WeavingStage.COMPLETED, WeavingStage.FAILED],
            "is_completed": self.current_stage == WeavingStage.COMPLETED,
            "is_failed": self.current_stage == WeavingStage.FAILED
        }
    
    def _get_stage_label(self) -> str:
        """获取当前阶段的中文标签"""
        labels = {
            WeavingStage.PREPARING: "准备阶段",
            WeavingStage.EXTRACTING_TEXT: "提取文本内容",
            WeavingStage.ANALYZING_MIND_CORE: "分析思维内核",
            WeavingStage.ANALYZING_EXPRESSION: "分析表达风格",
            WeavingStage.ANALYZING_DECISION: "分析决策逻辑",
            WeavingStage.ANALYZING_KNOWLEDGE: "分析知识领域",
            WeavingStage.ANALYZING_VALUES: "分析价值体系",
            WeavingStage.ANALYZING_EMOTION: "分析情感模式",
            WeavingStage.WEAVING_MIND: "编织思维内核",
            WeavingStage.GENERATING_IDENTITY: "生成身份卡",
            WeavingStage.COMPLETED: "编织完成",
            WeavingStage.FAILED: "编织失败"
        }
        return labels.get(self.current_stage, "未知阶段")


class WeavingSession(Base):
    """编织会话（用于 WebSocket 连接追踪）"""
    __tablename__ = "weaving_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatars.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # WebSocket 连接 ID
    connection_id = Column(String(100), nullable=True)
    
    # 会话状态
    is_active = Column(String(20), default="active")  # active, closed
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
