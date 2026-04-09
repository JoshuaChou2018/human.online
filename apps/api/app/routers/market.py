"""
分身市场路由
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.avatar import Avatar, AvatarType, AvatarStatus
from app.schemas.market import (
    MarketAvatarResponse, MarketAvatarListResponse, AvatarCategory,
    CloneAvatarRequest, CloneAvatarResponse, AvatarReviewCreate,
    AvatarReviewUpdate, AvatarReviewResponse, AvatarStats
)

router = APIRouter(prefix="/market", tags=["分身市场"])


@router.get("/categories", response_model=List[AvatarCategory])
async def get_categories():
    """获取分身分类列表"""
    return [
        AvatarCategory(id="tech", name="科技", icon="💻", description="科技领袖、程序员、产品经理"),
        AvatarCategory(id="business", name="商业", icon="💼", description="企业家、投资人、管理者"),
        AvatarCategory(id="philosophy", name="哲学", icon="🤔", description="哲学家、思想家、作家"),
        AvatarCategory(id="art", name="艺术", icon="🎨", description="艺术家、设计师、音乐人"),
        AvatarCategory(id="science", name="科学", icon="🔬", description="科学家、研究员、工程师"),
        AvatarCategory(id="history", name="历史", icon="📜", description="历史人物、名人"),
        AvatarCategory(id="entertainment", name="娱乐", icon="🎬", description="演员、导演、网红"),
        AvatarCategory(id="custom", name="用户创建", icon="👤", description="社区用户创建的分身"),
    ]


@router.get("/avatars", response_model=MarketAvatarListResponse)
async def list_market_avatars(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("popular", description="排序方式: popular, newest, rating, usage"),
    avatar_type: Optional[AvatarType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取市场分身列表
    
    支持筛选、搜索、排序
    """
    query = select(Avatar).where(
        and_(
            Avatar.is_public == True,
            Avatar.status == AvatarStatus.READY
        )
    )
    
    # 分类筛选
    if category:
        query = query.where(Avatar.cognitive_config["category"].astext == category)
    
    # 类型筛选
    if avatar_type:
        query = query.where(Avatar.avatar_type == avatar_type)
    
    # 搜索
    if search:
        search_filter = or_(
            Avatar.name.ilike(f"%{search}%"),
            Avatar.description.ilike(f"%{search}%"),
            Avatar.cognitive_config["tags"].astext.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    # 排序
    if sort_by == "popular":
        query = query.order_by(desc(Avatar.interaction_count))
    elif sort_by == "newest":
        query = query.order_by(desc(Avatar.created_at))
    elif sort_by == "rating":
        # 通过认知配置中的评分排序
        query = query.order_by(desc(Avatar.cognitive_config["rating"].astext))
    elif sort_by == "usage":
        query = query.order_by(desc(Avatar.interaction_count))
    else:
        query = query.order_by(desc(Avatar.created_at))
    
    # 获取总数
    count_query = select(func.count(Avatar.id)).where(
        and_(
            Avatar.is_public == True,
            Avatar.status == AvatarStatus.READY
        )
    )
    
    if category:
        count_query = count_query.where(Avatar.cognitive_config["category"].astext == category)
    if avatar_type:
        count_query = count_query.where(Avatar.avatar_type == avatar_type)
    if search:
        count_query = count_query.where(search_filter)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    avatars = result.scalars().all()
    
    # 转换为响应格式
    items = []
    for avatar in avatars:
        # 获取创建者信息
        creator_name = "Anonymous"
        if avatar.user_id:
            user_result = await db.execute(
                select(User).where(User.id == avatar.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user and user.username:
                creator_name = user.username
        
        # 获取统计信息
        cognitive_config = avatar.cognitive_config or {}
        
        items.append(MarketAvatarResponse(
            id=avatar.id,
            name=avatar.name,
            description=avatar.description,
            avatar_type=avatar.avatar_type,
            creator_name=creator_name,
            category=cognitive_config.get("category", "custom"),
            tags=cognitive_config.get("tags", []),
            rating=cognitive_config.get("rating", 0.0),
            usage_count=avatar.interaction_count,
            review_count=cognitive_config.get("review_count", 0),
            features=cognitive_config.get("mental_models", [])[:3],  # 只展示前3个特征
            is_featured=avatar.is_featured,
            created_at=avatar.created_at,
            estimated_tokens=cognitive_config.get("estimated_tokens", 0)
        ))
    
    return MarketAvatarListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/avatars/featured", response_model=List[MarketAvatarResponse])
async def get_featured_avatars(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取精选分身"""
    query = select(Avatar).where(
        and_(
            Avatar.is_public == True,
            Avatar.status == AvatarStatus.READY,
            Avatar.is_featured == True
        )
    ).limit(limit)
    
    result = await db.execute(query)
    avatars = result.scalars().all()
    
    items = []
    for avatar in avatars:
        creator_name = "Anonymous"
        if avatar.user_id:
            user_result = await db.execute(
                select(User).where(User.id == avatar.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                creator_name = user.username
        
        cognitive_config = avatar.cognitive_config or {}
        
        items.append(MarketAvatarResponse(
            id=avatar.id,
            name=avatar.name,
            description=avatar.description,
            avatar_type=avatar.avatar_type,
            creator_name=creator_name,
            category=cognitive_config.get("category", "custom"),
            tags=cognitive_config.get("tags", []),
            rating=cognitive_config.get("rating", 0.0),
            usage_count=avatar.interaction_count,
            review_count=cognitive_config.get("review_count", 0),
            features=cognitive_config.get("mental_models", [])[:3],
            is_featured=True,
            created_at=avatar.created_at,
            estimated_tokens=cognitive_config.get("estimated_tokens", 0)
        ))
    
    return items


@router.get("/avatars/{avatar_id}", response_model=MarketAvatarResponse)
async def get_market_avatar_detail(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取分身详情（市场视图）"""
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True,
                Avatar.status == AvatarStatus.READY
            )
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found or not available"
        )
    
    # 获取创建者信息
    creator_name = "Anonymous"
    creator_avatar = None
    if avatar.user_id:
        user_result = await db.execute(
            select(User).where(User.id == avatar.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user and user.username:
            creator_name = user.username
            creator_avatar = user.avatar_url
    
    cognitive_config = avatar.cognitive_config or {}
    expression_dna = cognitive_config.get("expression_dna", {})
    
    return MarketAvatarResponse(
        id=avatar.id,
        name=avatar.name,
        description=avatar.description,
        avatar_type=avatar.avatar_type,
        creator_name=creator_name,
        creator_avatar=creator_avatar,
        category=cognitive_config.get("category", "custom"),
        tags=cognitive_config.get("tags", []),
        rating=cognitive_config.get("rating", 0.0),
        usage_count=avatar.interaction_count,
        review_count=cognitive_config.get("review_count", 0),
        features=cognitive_config.get("mental_models", []),
        expression_dna=expression_dna,
        is_featured=avatar.is_featured,
        created_at=avatar.created_at,
        updated_at=avatar.updated_at,
        estimated_tokens=cognitive_config.get("estimated_tokens", 0),
        sample_dialogues=cognitive_config.get("sample_dialogues", [])
    )


@router.post("/avatars/{avatar_id}/clone", response_model=CloneAvatarResponse)
async def clone_avatar(
    avatar_id: UUID,
    request: CloneAvatarRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    克隆/使用市场分身
    
    创建一个基于公开分身的副本，用户可以进行个性化修改
    """
    # 查找原分身
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True,
                Avatar.status == AvatarStatus.READY
            )
        )
    )
    source_avatar = result.scalar_one_or_none()
    
    if not source_avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source avatar not found"
        )
    
    # 检查是否已克隆过
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.user_id == current_user.id,
                Avatar.cognitive_config["cloned_from"].astext == str(avatar_id)
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing and not request.force:
        return CloneAvatarResponse(
            success=False,
            message="You have already cloned this avatar",
            avatar_id=existing.id,
            already_cloned=True
        )
    
    # 创建克隆
    new_name = request.new_name or f"{source_avatar.name} (Clone)"
    
    cloned_avatar = Avatar(
        user_id=current_user.id,
        name=new_name,
        description=request.new_description or source_avatar.description,
        avatar_type=AvatarType.PERSONAL,
        status=AvatarStatus.READY,
        system_prompt=source_avatar.system_prompt,
        cognitive_config={
            **(source_avatar.cognitive_config or {}),
            "cloned_from": str(avatar_id),
            "cloned_at": datetime.utcnow().isoformat(),
            "cloned_by": str(current_user.id),
            "is_clone": True,
            "original_name": source_avatar.name,
            "custom_notes": request.custom_notes
        },
        style_config=source_avatar.style_config,
        expression_dna=source_avatar.expression_dna,
        is_public=False,  # 克隆默认为私有
    )
    
    db.add(cloned_avatar)
    
    # 更新原分身的克隆计数
    cognitive_config = source_avatar.cognitive_config or {}
    cognitive_config["clone_count"] = cognitive_config.get("clone_count", 0) + 1
    source_avatar.cognitive_config = cognitive_config
    
    await db.commit()
    await db.refresh(cloned_avatar)
    
    return CloneAvatarResponse(
        success=True,
        message="Avatar cloned successfully",
        avatar_id=cloned_avatar.id,
        already_cloned=False
    )


@router.get("/avatars/{avatar_id}/stats", response_model=AvatarStats)
async def get_avatar_stats(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取分身统计数据"""
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True
            )
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    cognitive_config = avatar.cognitive_config or {}
    
    return AvatarStats(
        total_conversations=cognitive_config.get("total_conversations", 0),
        total_messages=avatar.interaction_count,
        unique_users=cognitive_config.get("unique_users", 0),
        avg_session_duration=cognitive_config.get("avg_session_duration", 0),
        clone_count=cognitive_config.get("clone_count", 0),
        rating_distribution=cognitive_config.get("rating_distribution", {}),
        daily_usage=cognitive_config.get("daily_usage", [])
    )


@router.post("/avatars/{avatar_id}/reviews", response_model=AvatarReviewResponse)
async def create_review(
    avatar_id: UUID,
    review: AvatarReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建分身评价"""
    # 检查分身是否存在
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True
            )
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 检查是否已评价
    cognitive_config = avatar.cognitive_config or {}
    reviews = cognitive_config.get("reviews", [])
    
    for r in reviews:
        if r.get("user_id") == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this avatar"
            )
    
    # 添加评价
    new_review = {
        "user_id": str(current_user.id),
        "username": current_user.username or "用户" + str(current_user.id)[:8],
        "rating": review.rating,
        "comment": review.comment,
        "created_at": datetime.utcnow().isoformat()
    }
    
    reviews.append(new_review)
    
    # 更新评分
    total_rating = sum(r["rating"] for r in reviews)
    avg_rating = total_rating / len(reviews)
    
    cognitive_config["reviews"] = reviews
    cognitive_config["rating"] = round(avg_rating, 2)
    cognitive_config["review_count"] = len(reviews)
    
    avatar.cognitive_config = cognitive_config
    await db.commit()
    
    return AvatarReviewResponse(
        id=f"{avatar_id}_{current_user.id}",
        avatar_id=avatar_id,
        user_id=current_user.id,
        username=current_user.username or "用户" + str(current_user.id)[:8],
        rating=review.rating,
        comment=review.comment,
        created_at=datetime.utcnow()
    )


@router.get("/avatars/{avatar_id}/reviews", response_model=List[AvatarReviewResponse])
async def list_reviews(
    avatar_id: UUID,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取分身评价列表"""
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True
            )
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    cognitive_config = avatar.cognitive_config or {}
    reviews = cognitive_config.get("reviews", [])
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    paginated_reviews = reviews[start:end]
    
    return [
        AvatarReviewResponse(
            id=f"{avatar_id}_{r['user_id']}",
            avatar_id=avatar_id,
            user_id=UUID(r["user_id"]),
            username=r["username"],
            rating=r["rating"],
            comment=r.get("comment", ""),
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]) if r.get("updated_at") else None,
            is_owner=current_user is not None and r.get("user_id") == str(current_user.id)
        )
        for r in paginated_reviews
    ]


@router.put("/avatars/{avatar_id}/reviews", response_model=AvatarReviewResponse)
async def update_review(
    avatar_id: UUID,
    review: AvatarReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户对分身的评价
    
    - 只能更新自己的评价
    - 评分和评论都可以修改
    """
    # 检查分身是否存在
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True
            )
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 查找用户的评价
    cognitive_config = avatar.cognitive_config or {}
    reviews = cognitive_config.get("reviews", [])
    
    user_review = None
    review_index = -1
    for i, r in enumerate(reviews):
        if r.get("user_id") == str(current_user.id):
            user_review = r
            review_index = i
            break
    
    if user_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not reviewed this avatar yet"
        )
    
    # 更新评价
    reviews[review_index]["rating"] = review.rating
    reviews[review_index]["comment"] = review.comment or ""
    reviews[review_index]["updated_at"] = datetime.utcnow().isoformat()
    
    # 重新计算评分
    total_rating = sum(r["rating"] for r in reviews)
    avg_rating = total_rating / len(reviews)
    
    cognitive_config["reviews"] = reviews
    cognitive_config["rating"] = round(avg_rating, 2)
    
    avatar.cognitive_config = cognitive_config
    await db.commit()
    
    return AvatarReviewResponse(
        id=f"{avatar_id}_{current_user.id}",
        avatar_id=avatar_id,
        user_id=current_user.id,
        username=current_user.username or "用户" + str(current_user.id)[:8],
        rating=review.rating,
        comment=review.comment or "",
        created_at=datetime.fromisoformat(user_review["created_at"]),
        updated_at=datetime.fromisoformat(reviews[review_index]["updated_at"])
    )


@router.delete("/avatars/{avatar_id}/reviews", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除当前用户对分身的评价
    
    - 只能删除自己的评价
    """
    # 检查分身是否存在
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True
            )
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 查找并删除用户的评价
    cognitive_config = avatar.cognitive_config or {}
    reviews = cognitive_config.get("reviews", [])
    
    original_len = len(reviews)
    reviews = [r for r in reviews if r.get("user_id") != str(current_user.id)]
    
    if len(reviews) == original_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not reviewed this avatar yet"
        )
    
    # 重新计算评分
    if reviews:
        total_rating = sum(r["rating"] for r in reviews)
        avg_rating = total_rating / len(reviews)
        cognitive_config["rating"] = round(avg_rating, 2)
    else:
        cognitive_config["rating"] = 0.0
    
    cognitive_config["reviews"] = reviews
    cognitive_config["review_count"] = len(reviews)
    
    avatar.cognitive_config = cognitive_config
    await db.commit()
    
    return None


@router.get("/avatars/{avatar_id}/my-review", response_model=Optional[AvatarReviewResponse])
async def get_my_review(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户对分身的评价
    
    - 如果用户没有评价过，返回 null
    - 用于前端判断用户是否可以评价或修改评价
    """
    # 检查分身是否存在
    result = await db.execute(
        select(Avatar).where(
            and_(
                Avatar.id == avatar_id,
                Avatar.is_public == True
            )
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 查找用户的评价
    cognitive_config = avatar.cognitive_config or {}
    reviews = cognitive_config.get("reviews", [])
    
    for r in reviews:
        if r.get("user_id") == str(current_user.id):
            return AvatarReviewResponse(
                id=f"{avatar_id}_{current_user.id}",
                avatar_id=avatar_id,
                user_id=current_user.id,
                username=current_user.username or r.get("username") or "用户" + str(current_user.id)[:8],
                rating=r["rating"],
                comment=r.get("comment", ""),
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"]) if r.get("updated_at") else None,
                is_owner=True
            )
    
    return None
