"""
数字分身相关路由
支持多 LLM 提供商
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.avatar import Avatar, DataSource, AvatarType, AvatarStatus, DataSourceType, DataSourceStatus
from app.schemas.avatar import (
    AvatarCreate, AvatarUpdate, AvatarResponse, AvatarListResponse,
    DataSourceCreate, DataSourceResponse, WeaveProgress
)
from app.services.avatar import (
    create_avatar_for_user, get_user_avatars, delete_avatar as delete_avatar_service,
    rebuild_avatar
)
from app.services.avatar_from_text import create_avatar_from_text_description
from app.services.storage import save_upload_file
from app.services.mindweave import start_weaving_task

router = APIRouter(prefix="/avatars", tags=["数字分身"])


@router.post("", response_model=AvatarResponse, status_code=status.HTTP_201_CREATED)
async def create_avatar(
    data: AvatarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的数字分身（基础版本）"""
    avatar = Avatar(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        avatar_type=data.avatar_type,
        status=AvatarStatus.DRAFT
    )
    
    db.add(avatar)
    await db.commit()
    await db.refresh(avatar)
    
    return avatar


@router.post("/from-data", response_model=AvatarResponse, status_code=status.HTTP_201_CREATED)
async def create_avatar_from_data(
    name: str = Form(..., min_length=1, max_length=100),
    description: Optional[str] = Form(None),
    data_source_ids: str = Form(..., description="逗号分隔的数据源 ID 列表"),
    is_public: bool = Form(True, description="是否公开分身（公开会加入沙盒、市场和观察者模式）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从用户数据源创建数字分身
    
    - 检查用户免费额度
    - 自动关联数据源
    - 公开分身自动加入沙盒、市场和观察者模式
    """
    # 解析数据源 ID
    source_ids = [s.strip() for s in data_source_ids.split(",") if s.strip()]
    
    if not source_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one data source is required"
        )
    
    avatar = await create_avatar_for_user(
        user=current_user,
        name=name,
        description=description,
        data_source_ids=source_ids,
        is_public=is_public,
        db=db
    )
    
    return avatar


@router.post("/from-description", response_model=AvatarResponse, status_code=status.HTTP_201_CREATED)
async def create_avatar_from_description(
    name: str = Form(..., min_length=1, max_length=100, description="分身名称"),
    description: str = Form(..., min_length=10, max_length=2000, description="分身描述，越详细越好"),
    is_public: bool = Form(True, description="是否公开分身（公开会加入沙盒、市场和观察者模式）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    基于文本描述创建数字分身（无需上传数据）
    
    用户只需提供一段文本描述，例如：
    - "创建一个像乔布斯一样追求完美、有现实扭曲力场的科技领袖"
    - "我想创建一个温柔、善解人意的心理咨询师分身"
    - "创建一个精通中国历史、说话文绉绉的学者"
    
    后端将使用 AI 自动分析描述并生成完整的分身配置，包括：
    - 系统提示词（定义性格和说话风格）
    - MindWeave 六维认知特征
    - 认知配置和表达 DNA
    - LLM 样式参数
    
    然后自动进入编织流程，约 5-10 秒后即可使用。
    """
    avatar = await create_avatar_from_text_description(
        user=current_user,
        name=name,
        description=description,
        is_public=is_public,
        db=db
    )
    
    return avatar


@router.get("/my/avatars", response_model=List[AvatarResponse])
async def get_my_avatars(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有 psyche"""
    avatars = await get_user_avatars(current_user, db)
    return avatars


@router.get("", response_model=AvatarListResponse)
async def list_avatars(
    type: Optional[AvatarType] = None,
    status: Optional[AvatarStatus] = None,
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取数字分身列表"""
    query = select(Avatar)
    
    # 构建过滤条件
    filters = []
    
    # 默认排除已归档的分身，除非明确指定了状态
    if status:
        filters.append(Avatar.status == status)
    else:
        filters.append(Avatar.status != AvatarStatus.ARCHIVED)
    
    if type:
        filters.append(Avatar.avatar_type == type)
    
    if is_public is not None:
        filters.append(Avatar.is_public == is_public)
    
    # 搜索条件
    if search:
        filters.append(
            or_(
                Avatar.name.ilike(f"%{search}%"),
                Avatar.description.ilike(f"%{search}%")
            )
        )
    
    # 权限过滤：用户可以看到自己的分身 + 公开的分身
    if current_user:
        filters.append(
            or_(
                Avatar.user_id == current_user.id,
                Avatar.is_public == True
            )
        )
    else:
        filters.append(Avatar.is_public == True)
    
    if filters:
        query = query.where(and_(*filters))
    
    # 排序
    query = query.order_by(Avatar.created_at.desc())
    
    # 分页
    total_query = select(Avatar).where(and_(*filters)) if filters else select(Avatar)
    total_result = await db.execute(total_query)
    total = len(total_result.scalars().all())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/featured", response_model=List[AvatarResponse])
async def get_featured_avatars(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取推荐的名人分身"""
    query = select(Avatar).where(
        and_(
            Avatar.is_featured == True,
            Avatar.status == AvatarStatus.READY,
            Avatar.is_public == True
        )
    ).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{avatar_id}", response_model=AvatarResponse)
async def get_avatar(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取单个数字分身详情"""
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 检查权限
    if not avatar.is_public and (not current_user or avatar.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this avatar"
        )
    
    return avatar


@router.put("/{avatar_id}", response_model=AvatarResponse)
async def update_avatar(
    avatar_id: UUID,
    data: AvatarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数字分身信息"""
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    if avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this avatar"
        )
    
    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(avatar, field, value)
    
    await db.commit()
    await db.refresh(avatar)
    
    return avatar


@router.delete("/{avatar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar_endpoint(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数字分身（归档）"""
    success = await delete_avatar_service(str(avatar_id), current_user, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    return None


@router.post("/{avatar_id}/rebuild", response_model=AvatarResponse)
async def rebuild_avatar_endpoint(
    avatar_id: UUID,
    data_source_ids: Optional[str] = Form(None, description="逗号分隔的新数据源 ID 列表，不传则使用原有数据"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重建数字分身
    
    - 可以更换数据源
    - 重置编织状态
    - 自动加入沙盒
    """
    source_ids = None
    if data_source_ids:
        source_ids = [s.strip() for s in data_source_ids.split(",") if s.strip()]
    
    avatar = await rebuild_avatar(
        avatar_id=str(avatar_id),
        user=current_user,
        data_source_ids=source_ids,
        db=db
    )
    
    return avatar


@router.post("/{avatar_id}/data-sources", response_model=AvatarResponse)
async def update_avatar_data_sources(
    avatar_id: UUID,
    data_source_ids: str = Form(..., description="逗号分隔的数据源 ID 列表"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新分身使用的数据源
    """
    from app.services.avatar import rebuild_avatar
    
    source_ids = [s.strip() for s in data_source_ids.split(",") if s.strip()]
    
    if not source_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one data source is required"
        )
    
    avatar = await rebuild_avatar(
        avatar_id=str(avatar_id),
        user=current_user,
        data_source_ids=source_ids,
        db=db
    )
    
    return avatar


@router.post("/{avatar_id}/visibility", response_model=AvatarResponse)
async def update_avatar_visibility(
    avatar_id: UUID,
    is_public: bool = Form(..., description="是否公开"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新分身公开/私有状态
    - 公开：加入沙盒
    - 私有：从沙盒移除
    """
    result = await db.execute(
        select(Avatar).where(
            Avatar.id == avatar_id,
            Avatar.user_id == current_user.id
        )
    )
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 更新公开状态
    avatar.is_public = is_public
    avatar.auto_join_sandbox = is_public
    
    # 根据公开状态处理沙盒
    if is_public:
        # 公开：加入沙盒
        avatar.sandbox_status = "active"
        from app.services.avatar import add_avatar_to_sandbox
        await add_avatar_to_sandbox(avatar, db)
    else:
        # 私有：从沙盒移除
        avatar.sandbox_status = "inactive"
        from app.services.avatar import remove_avatar_from_sandbox
        await remove_avatar_from_sandbox(str(avatar_id), db)
    
    await db.commit()
    await db.refresh(avatar)
    
    return avatar


@router.post("/{avatar_id}/weave", response_model=dict)
async def start_weaving(
    avatar_id: UUID,
    provider: Optional[str] = Query(None, description="LLM 提供商 (openai | kimi | anthropic)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    开始思维编织流程
    
    基于 MindWeave 理论，从数据源中提取六维思维线索，编织成数字 psyche。
    
    可选指定 LLM 提供商:
    - openai: GPT-4, GPT-3.5 (默认)
    - kimi: Moonshot, 超长上下文, 中文优化
    """
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    if avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # 检查是否有数据源
    result = await db.execute(
        select(DataSource).where(
            and_(
                DataSource.avatar_id == avatar_id,
                DataSource.status == DataSourceStatus.COMPLETED
            )
        )
    )
    data_sources = result.scalars().all()
    
    if not data_sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed data sources found. Please upload data first."
        )
    
    # 验证提供商
    if provider:
        from app.services.llm import llm_manager, LLMProvider
        try:
            provider_enum = LLMProvider(provider.lower())
            if provider_enum not in llm_manager.get_available_providers():
                available = [p.value for p in llm_manager.get_available_providers()]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Provider '{provider}' not available. Available: {available}"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider '{provider}'. Use: openai, kimi, anthropic"
            )
    
    # 更新状态
    avatar.status = AvatarStatus.WEAVING
    await db.commit()
    
    # 启动异步任务
    task_id = await start_weaving_task(
        avatar_id, 
        [str(ds.id) for ds in data_sources],
        provider
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Mind weaving process started",
        "provider": provider or "default"
    }


@router.get("/{avatar_id}/status", response_model=WeaveProgress)
async def get_weaving_status(
    avatar_id: UUID,
    detailed: bool = Query(False, description="是否返回详细进度信息"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取编织进度
    
    Args:
        detailed: 如果为 true，返回完整的编织进度信息（包括日志、中间结果等）
    """
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    if avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # 获取认知配置中的提供商信息
    cognitive_config = avatar.cognitive_config or {}
    provider_used = cognitive_config.get("provider_used")
    
    # 计算进度
    if avatar.status == AvatarStatus.READY:
        progress = 100.0
        current_step = "completed"
        completed_steps = ["extracted", "analyzed", "weaved", "ready"]
    elif avatar.status == AvatarStatus.WEAVING:
        progress = 50.0
        current_step = "weaving"
        completed_steps = ["extracted"]
    else:
        progress = 0.0
        current_step = "pending"
        completed_steps = []
    
    response = WeaveProgress(
        status=avatar.status,
        progress=progress,
        current_step=current_step,
        completed_steps=completed_steps,
        provider=provider_used
    )
    
    # 如果请求详细信息，查询 WeavingProgress 表
    if detailed:
        from app.models.weaving_progress import WeavingProgress
        
        result = await db.execute(
            select(WeavingProgress).where(WeavingProgress.avatar_id == avatar_id)
        )
        weaving_progress = result.scalar_one_or_none()
        
        if weaving_progress:
            from app.schemas.avatar import WeavingDetailedProgress
            response.detailed_progress = WeavingDetailedProgress(**weaving_progress.to_dict())
    
    return response


@router.get("/weaving/stages")
async def get_weaving_stages():
    """获取所有编织阶段信息
    
    返回 MindWeave 编织各阶段的详细信息，用于前端展示
    """
    from app.services.weaving_tracker import STAGE_DESCRIPTIONS
    from app.models.weaving_progress import WeavingStage
    
    stages = []
    for stage in WeavingStage:
        if stage in [WeavingStage.COMPLETED, WeavingStage.FAILED]:
            continue
        info = STAGE_DESCRIPTIONS.get(stage, {})
        stages.append({
            "key": stage.value,
            "title": info.get("title", stage.value),
            "description": info.get("description", ""),
            "icon": info.get("icon", "🔄")
        })
    
    return {"stages": stages}


@router.get("/{avatar_id}/identity")
async def get_avatar_identity(
    avatar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取数字分身的身份卡信息（MindWeave 分析结果）
    
    权限说明：
    - 公开分身：任何人可以查看公开的六维特征
    - 私有分身：仅创建者可见
    - 隐私信息：仅创建者可见（包括偏好、背景等）
    """
    result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
    avatar = result.scalar_one_or_none()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # 检查权限：公开分身或所有者
    if not avatar.is_public and (not current_user or avatar.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this avatar's identity"
        )
    
    # 检查是否是创建者
    is_owner = current_user and avatar.user_id == current_user.id
    
    # 获取 mind_weave_profile
    mind_profile = avatar.mind_weave_profile or {}
    
    # 如果还没有分析结果，触发分析
    if not mind_profile or not mind_profile.get("identityCard"):
        from app.services.mindweave_analyzer import analyze_mindweave_features, generate_identity_card
        
        mind_threads = await analyze_mindweave_features(avatar, db)
        identity_card = await generate_identity_card(avatar, mind_threads)
        
        mind_profile = {
            "mindThreads": mind_threads,
            "identityCard": identity_card,
            "analyzedAt": datetime.utcnow().isoformat()
        }
        
        avatar.mind_weave_profile = mind_profile
        await db.commit()
    
    # 获取或重新生成身份卡（确保数据格式正确）
    identity_card = mind_profile.get("identityCard", {})
    if not identity_card:
        # 如果身份卡为空，尝试从 mindThreads 重新生成
        mind_threads = mind_profile.get("mindThreads", {})
        if mind_threads:
            from app.services.mindweave_analyzer import generate_identity_card
            identity_card = await generate_identity_card(avatar, mind_threads)
            # 更新数据库
            mind_profile["identityCard"] = identity_card
            avatar.mind_weave_profile = mind_profile
            await db.commit()
    
    # 确保 mindThreads 格式正确（兼容旧格式）
    mind_threads = mind_profile.get("mindThreads", {})
    # 如果是旧格式（嵌套在 mindThreads 下），转换为平铺格式
    if "core" in mind_threads and "mindCore" not in mind_threads:
        mind_threads = {
            "mindCore": mind_threads.get("core", {}),
            "expressionStyle": mind_threads.get("expression", {}),
            "decisionLogic": mind_threads.get("decision", {}),
            "knowledgeAreas": mind_threads.get("knowledge", []),
            "valueSystem": mind_threads.get("values", {}),
            "emotionalPattern": mind_threads.get("emotional", {}),
        }
    
    # 构建返回结果
    response = {
        "mindThreads": mind_threads,
        "identityCard": identity_card,
        "analyzedAt": mind_profile.get("analyzedAt"),
        "isOwner": is_owner,  # 是否是创建者
    }
    
    # 只有创建者才能看到隐私信息
    if is_owner:
        private_profile = avatar.private_profile or {}
        response["privateInfo"] = {
            "preferences": private_profile.get("preferences", []),
            "background": private_profile.get("background", []),
            "personalTraits": private_profile.get("personal_traits", []),
            "sensitiveInfo": private_profile.get("sensitive_info", []),
            "summary": private_profile.get("summary", ""),
            "extractedAt": private_profile.get("extracted_at"),
        }
        response["hasPrivateInfo"] = bool(private_profile) and private_profile.get("preferences") or private_profile.get("background")
    else:
        response["hasPrivateInfo"] = False
    
    return response
