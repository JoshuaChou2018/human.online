"""
Google OAuth 处理
"""
import secrets
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.auth.jwt import create_user_token


# Google OAuth 端点
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_auth_url(state: Optional[str] = None) -> str:
    """生成 Google OAuth 授权 URL"""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )
    
    # 生成 state 防止 CSRF
    if state is None:
        state = secrets.token_urlsafe(32)
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{GOOGLE_AUTH_URL}?{query_string}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """用授权码交换 access token"""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code for token: {response.text}"
        )
    
    return response.json()


async def get_google_user_info(access_token: str) -> Dict[str, Any]:
    """获取 Google 用户信息"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google"
        )
    
    return response.json()


async def handle_google_callback(
    code: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    处理 Google OAuth 回调
    返回用户信息和 JWT token
    """
    # 1. 交换授权码获取 token
    token_data = await exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    # 2. 获取用户信息
    user_info = await get_google_user_info(access_token)
    
    google_id = user_info.get("id")
    email = user_info.get("email")
    display_name = user_info.get("name")
    avatar_url = user_info.get("picture")
    
    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user info from Google"
        )
    
    # 3. 查找或创建用户
    result = await db.execute(
        select(User).where(User.google_id == google_id)
    )
    user = result.scalar_one_or_none()
    
    is_new_user = False
    
    if user is None:
        # 检查 email 是否已被使用
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # 关联 Google 账号到现有用户
            existing_user.google_id = google_id
            existing_user.google_access_token = access_token
            existing_user.google_refresh_token = refresh_token
            if not existing_user.avatar_url:
                existing_user.avatar_url = avatar_url
            user = existing_user
        else:
            # 创建新用户
            user = User(
                email=email,
                google_id=google_id,
                google_access_token=access_token,
                google_refresh_token=refresh_token,
                display_name=display_name,
                avatar_url=avatar_url,
                is_verified=True,  # Google 邮箱已验证
                free_avatar_quota=1,  # 免费创建一个分身
            )
            db.add(user)
            is_new_user = True
    else:
        # 更新 token
        user.google_access_token = access_token
        if refresh_token:  # 只有第一次或重新授权时才会返回 refresh_token
            user.google_refresh_token = refresh_token
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    # 4. 生成 JWT token
    jwt_token = create_user_token(user)
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_new_user": is_new_user,
            "can_create_free_avatar": user.can_create_free_avatar,
            "remaining_free_quota": user.remaining_free_quota,
        }
    }


async def refresh_google_token(user: User) -> Optional[str]:
    """刷新 Google access token"""
    if not user.google_refresh_token:
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": user.google_refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    
    return None
