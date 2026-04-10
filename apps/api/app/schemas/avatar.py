"""
数字分身相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class AvatarType(str, Enum):
    PERSONAL = "personal"
    CELEBRITY = "celebrity"
    SYSTEM = "system"


class AvatarStatus(str, Enum):
    DRAFT = "draft"
    WEAVING = "weaving"  # 思维编织中
    READY = "ready"
    ARCHIVED = "archived"


class LLMProvider(str, Enum):
    """支持的 LLM 提供商"""
    OPENAI = "openai"
    KIMI = "kimi"
    ANTHROPIC = "anthropic"
    AZURE = "azure"


class CognitiveProfile(BaseModel):
    expression_dna: Dict[str, Any] = Field(default_factory=dict)
    mental_models: List[Dict[str, Any]] = Field(default_factory=list)
    decision_heuristics: List[Dict[str, Any]] = Field(default_factory=list)
    value_boundaries: List[str] = Field(default_factory=list)
    knowledge_boundaries: List[str] = Field(default_factory=list)
    relationship_patterns: Dict[str, Any] = Field(default_factory=dict)
    # 多模型支持
    provider_used: Optional[str] = None
    model_used: Optional[str] = None


class StyleParams(BaseModel):
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.9, ge=0, le=1)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)
    presence_penalty: float = Field(default=0, ge=-2, le=2)
    max_tokens: int = Field(default=1000, ge=1, le=8000)


class AvatarCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    avatar_type: AvatarType = AvatarType.PERSONAL


class AvatarUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    cognitive_config: Optional[Dict[str, Any]] = None
    style_config: Optional[StyleParams] = None
    is_public: Optional[bool] = None


class AvatarResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    avatar_type: AvatarType
    status: AvatarStatus
    cognitive_profile: Optional[CognitiveProfile] = None
    style_params: StyleParams = Field(default_factory=StyleParams)
    interaction_count: int = 0
    knowledge_chunks_count: int = 0
    is_public: bool = False
    is_featured: bool = False
    mind_weave_profile: Optional[Dict[str, Any]] = None  # MindWeave 分析结果
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AvatarListResponse(BaseModel):
    items: List[AvatarResponse]
    total: int
    page: int
    page_size: int


class WeavingLogEntry(BaseModel):
    """编织日志条目"""
    timestamp: str
    stage: str
    message: str
    type: str = "info"  # info, success, warning, error
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WeavingStageProgress(BaseModel):
    """编织阶段进度"""
    progress: float = Field(..., ge=0, le=100)
    status: str = "running"  # running, completed, failed
    updated_at: str


class WeavingStageInfo(BaseModel):
    """编织阶段信息"""
    key: str
    title: str
    description: str
    icon: str


class WeavingDetailedProgress(BaseModel):
    """详细编织进度（用于实时监控页面）"""
    id: str
    avatar_id: str
    current_stage: Optional[str]
    current_stage_label: str
    overall_progress: float = Field(..., ge=0, le=100)
    stage_progress: Dict[str, WeavingStageProgress] = Field(default_factory=dict)
    logs: List[WeavingLogEntry] = Field(default_factory=list)
    current_text_preview: Optional[str] = None
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    llm_stats: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[str] = None
    is_running: bool = False
    is_completed: bool = False
    is_failed: bool = False


class WeaveProgress(BaseModel):
    status: AvatarStatus
    progress: float = Field(..., ge=0, le=100)
    current_step: str
    completed_steps: List[str] = Field(default_factory=list)
    estimated_time_remaining: Optional[int] = None  # seconds
    provider: Optional[str] = None  # 使用的 LLM 提供商
    
    # 详细进度信息（可选）
    detailed_progress: Optional[WeavingDetailedProgress] = None


class DataSourceType(str, Enum):
    CHAT = "chat"
    DOCUMENT = "document"
    SOCIAL = "social"
    AUDIO = "audio"


class DataSourceStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSourceCreate(BaseModel):
    source_type: DataSourceType
    file_name: str
    mime_type: Optional[str] = None


class DataSourceResponse(BaseModel):
    id: UUID
    avatar_id: UUID
    source_type: DataSourceType
    file_name: str
    file_size: int
    mime_type: Optional[str]
    status: DataSourceStatus
    processing_progress: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_insights: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[UUID] = None
    provider: Optional[str] = None  # 可选指定 LLM 提供商


class ChatMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender_name: str
    content: str
    is_user: bool = False  # 是否是用户发送的消息
    emotion_state: Optional[Dict[str, float]] = None
    provider_used: Optional[str] = None  # 实际使用的 LLM 提供商
    created_at: datetime


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    provider: Optional[str] = Field(None, description="LLM 提供商 (openai | kimi | anthropic)")
    stream: bool = False
