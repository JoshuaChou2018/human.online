"""
认证路由 - 邮箱/密码登录
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.core.database import get_db
from app.auth import (
    get_current_user, verify_password, get_password_hash, create_access_token
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


# ============ 请求/响应模型 ============

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    can_create_free_avatar: bool
    remaining_free_quota: int
    avatars_created: int
    free_avatar_quota: int


# ============ 邮箱注册/登录 ============

@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == request.email))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建新用户
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        display_name=request.display_name or request.email.split('@')[0],
        is_verified=True,  # 简化流程，默认已验证
        free_avatar_quota=1,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 生成 token
    token = create_access_token({"sub": str(user.id), "email": user.email})
    
    return TokenResponse(
        access_token=token,
        user={
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_new_user": True,
            "can_create_free_avatar": user.can_create_free_avatar,
            "remaining_free_quota": user.remaining_free_quota,
            "avatars_created": user.avatars_created,
            "free_avatar_quota": user.free_avatar_quota,
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # 生成 token
    token = create_access_token({"sub": str(user.id), "email": user.email})
    
    return TokenResponse(
        access_token=token,
        user={
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_new_user": False,
            "can_create_free_avatar": user.can_create_free_avatar,
            "remaining_free_quota": user.remaining_free_quota,
            "avatars_created": user.avatars_created,
            "free_avatar_quota": user.free_avatar_quota,
        }
    )


@router.post("/demo", response_model=TokenResponse)
async def demo_login(db: AsyncSession = Depends(get_db)):
    """
    Demo 账号快速登录
    自动创建或使用已有的 demo 账号
    Demo 用户有 3 个免费额度
    """
    demo_email = "demo@humanonline.ai"
    demo_password = "demo123456"
    
    # 查找 demo 用户
    result = await db.execute(select(User).where(User.email == demo_email))
    user = result.scalar_one_or_none()
    
    if not user:
        # 创建 demo 用户，给予 3 个免费额度
        user = User(
            email=demo_email,
            password_hash=get_password_hash(demo_password),
            display_name="Demo User",
            is_verified=True,
            free_avatar_quota=3,  # Demo 用户给 3 个额度
            avatars_created=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        is_new = True
    else:
        is_new = False
        # 确保 demo 用户有正确的额度设置
        if user.free_avatar_quota != 3:
            user.free_avatar_quota = 3
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # 生成 token
    token = create_access_token({"sub": str(user.id), "email": user.email})
    
    return TokenResponse(
        access_token=token,
        user={
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_new_user": is_new,
            "can_create_free_avatar": user.can_create_free_avatar,
            "remaining_free_quota": user.remaining_free_quota,
            "avatars_created": user.avatars_created,
            "free_avatar_quota": user.free_avatar_quota,
        }
    )


# ============ 当前用户 ============

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        can_create_free_avatar=current_user.can_create_free_avatar,
        remaining_free_quota=current_user.remaining_free_quota,
        avatars_created=current_user.avatars_created,
        free_avatar_quota=current_user.free_avatar_quota,
    )


@router.post("/logout")
async def logout():
    """登出（前端只需删除 token）"""
    return {"message": "Logged out successfully"}


# ============ 配额检查 ============

@router.get("/quota")
async def get_quota(current_user: User = Depends(get_current_user)):
    """获取用户配额信息"""
    return {
        "free_quota": current_user.free_avatar_quota,
        "used": current_user.avatars_created,
        "remaining": current_user.remaining_free_quota,
        "can_create": current_user.can_create_free_avatar,
    }
