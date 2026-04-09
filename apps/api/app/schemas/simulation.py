"""
社会模拟相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from enum import Enum


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReactionType(str, Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    AMPLIFY = "amplify"
    QUESTION = "question"
    IGNORE = "ignore"


class SimulationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    initial_message: str = Field(..., min_length=1, max_length=5000)
    initiator_avatar_id: UUID
    avatar_ids: List[UUID] = Field(default_factory=list)
    max_steps: int = Field(default=10, ge=1, le=50, description="Maximum propagation steps (1-50)")


class PropagationEvent(BaseModel):
    step: int
    from_avatar_id: UUID
    from_avatar_name: str
    to_avatar_id: UUID
    to_avatar_name: str
    reaction_type: ReactionType
    reaction_content: Optional[str] = None
    influence_probability: float


class SimulationResult(BaseModel):
    message_id: str = ""
    content: str = ""
    total_reach: int = 0
    propagation_steps: int = 0
    sentiment_evolution: List[Tuple[int, float]] = []
    key_influencers: List[str] = []
    reaction_distribution: Dict[str, int] = {}
    polarization: float = 0.0


class VisualizationNode(BaseModel):
    id: str
    name: str
    influence: float
    emotion: Dict[str, float]
    reaction: str
    activation_step: int


class VisualizationEdge(BaseModel):
    source: str
    target: str
    step: int
    probability: float
    reaction: str


class VisualizationData(BaseModel):
    nodes: List[VisualizationNode]
    edges: List[VisualizationEdge]
    timeline: List[Tuple[int, float]]
    stats: Dict[str, Any]


class SimulationResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    user_id: UUID
    initial_message: str
    initiator_avatar_id: UUID
    avatar_ids: List[UUID]
    max_steps: int = 10
    status: SimulationStatus
    result: Optional[SimulationResult] = None
    visualization: Optional[VisualizationData] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    @field_validator('result', mode='before')
    @classmethod
    def validate_result(cls, v):
        """将空字典转换为 None"""
        if v == {} or v == []:
            return None
        return v
    
    @field_validator('visualization', mode='before')
    @classmethod
    def validate_visualization(cls, v):
        """将空字典转换为 None"""
        if v == {} or v == []:
            return None
        return v
    
    class Config:
        from_attributes = True


class SimulationListResponse(BaseModel):
    items: List[SimulationResponse]
    total: int
    page: int
    page_size: int


class SimulationStepRequest(BaseModel):
    message: str
    current_step: int = 0


class SimulationStartRequest(BaseModel):
    max_steps: int = Field(default=10, ge=1, le=50, description="Maximum propagation steps (1-50)")


class ThinkingProcess(BaseModel):
    step: int
    avatar_id: str
    avatar_name: str
    thinking: str


class SimulationResult(BaseModel):
    message_id: str = ""
    content: str = ""
    total_reach: int = 0
    propagation_steps: int = 0
    sentiment_evolution: List[Tuple[int, float]] = []
    key_influencers: List[str] = []
    reaction_distribution: Dict[str, int] = {}
    polarization: float = 0.0
    thinking_processes: List[ThinkingProcess] = []


class CounterfactualRequest(BaseModel):
    """反事实模拟请求"""
    preset: Optional[str] = Field(None, description="预设场景ID")
    custom_event: Optional[str] = Field(None, description="自定义事件内容")
    avatar_ids: List[str] = Field(..., description="参与者Avatar ID列表")
    initiator_id: Optional[str] = Field(None, description="发起者Avatar ID")
    max_steps: int = Field(default=10, ge=1, le=50, description="最大传播轮数")
    max_rounds: int = Field(default=3, ge=1, le=20, description="最大对话轮数")


class CounterfactualResponse(BaseModel):
    """反事实模拟响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# 流式模拟事件类型
class StreamEventType(str, Enum):
    START = "start"           # 模拟开始
    NODE_ACTIVATE = "node_activate"  # 节点被激活
    MESSAGE = "message"       # 生成消息
    THINKING = "thinking"     # 思考过程
    EDGE_CREATE = "edge_create"  # 创建传播边
    STEP_COMPLETE = "step_complete"  # 步骤完成
    COMPLETE = "complete"     # 模拟完成
    ERROR = "error"           # 错误


class SimulationStreamEvent(BaseModel):
    """流式模拟事件"""
    type: StreamEventType
    step: int
    round: int
    data: Dict[str, Any]
    timestamp: str
