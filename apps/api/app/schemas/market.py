"""
分身市场相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.avatar import AvatarType


class AvatarCategory(BaseModel):
    """分身分类"""
    id: str
    name: str
    icon: str
    description: str
    avatar_count: Optional[int] = None


class MarketAvatarResponse(BaseModel):
    """市场分身响应"""
    id: UUID
    name: str
    description: Optional[str] = None
    avatar_type: AvatarType
    creator_name: str
    creator_avatar: Optional[str] = None
    category: str = "custom"
    tags: List[str] = Field(default_factory=list)
    rating: float = 0.0
    usage_count: int = 0
    review_count: int = 0
    features: List[Dict[str, Any]] = Field(default_factory=list)
    expression_dna: Optional[Dict[str, Any]] = None
    is_featured: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    estimated_tokens: int = 0
    sample_dialogues: Optional[List[Dict[str, str]]] = None


class MarketAvatarListResponse(BaseModel):
    """市场分身列表响应"""
    items: List[MarketAvatarResponse]
    total: int
    page: int
    page_size: int


class CloneAvatarRequest(BaseModel):
    """克隆分身请求"""
    new_name: Optional[str] = None
    new_description: Optional[str] = None
    custom_notes: Optional[str] = None
    force: bool = False  # 如果已克隆过，是否强制重新克隆


class CloneAvatarResponse(BaseModel):
    """克隆分身响应"""
    success: bool
    message: str
    avatar_id: UUID
    already_cloned: bool = False


class AvatarReviewCreate(BaseModel):
    """创建评价请求"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class AvatarReviewUpdate(BaseModel):
    """更新评价请求"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class AvatarReviewResponse(BaseModel):
    """评价响应"""
    id: str
    avatar_id: UUID
    user_id: UUID
    username: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_owner: bool = False  # 是否为当前用户的评价


class AvatarStats(BaseModel):
    """分身统计数据"""
    total_conversations: int = 0
    total_messages: int = 0
    unique_users: int = 0
    avg_session_duration: float = 0.0
    clone_count: int = 0
    rating_distribution: Dict[str, int] = Field(default_factory=dict)
    daily_usage: List[Dict[str, Any]] = Field(default_factory=list)


class MarketSearchSuggestion(BaseModel):
    """搜索建议"""
    query: str
    type: str  # "name", "tag", "category", "creator"
    count: Optional[int] = None
