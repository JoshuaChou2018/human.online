"""
Human.online API 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings, check_llm_config
from app.core.database import init_db, close_db, init_mongodb, close_mongodb, init_redis, close_redis
from app.routers import auth, avatars, data_sources, conversations, simulations, websocket, market, user_data, sandbox, counterfactual
from app.services.llm import init_llm_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 Starting up...")
    
    # 检查配置
    print("🔍 Checking configuration...")
    check_llm_config()
    
    # 初始化数据库
    await init_db()
    await init_mongodb()
    await init_redis()
    print("✅ Database connections initialized")
    
    # 初始化 LLM 客户端
    print("🤖 Initializing LLM clients...")
    try:
        init_llm_clients()
        print("✅ LLM clients initialized")
    except RuntimeError as e:
        print(f"⚠️  {e}")
        print("   Application will start but LLM features will not work.")
    
    yield
    
    # 关闭时
    print("🛑 Shutting down...")
    
    await close_db()
    await close_mongodb()
    await close_redis()
    
    print("✅ All connections closed")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="数字分身社交平台 API - 支持 OpenAI, Kimi, Claude 等多种 LLM",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查
@app.get("/health")
async def health_check():
    from app.services.llm import llm_manager, LLMProvider
    
    available_providers = llm_manager.get_available_providers()
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "llm_providers": [p.value for p in available_providers],
        "default_provider": llm_manager._default_provider.value if llm_manager._default_provider else None
    }


# LLM 提供商信息
@app.get("/llm/providers")
async def list_llm_providers():
    """获取可用的 LLM 提供商列表"""
    from app.services.llm import llm_manager, LLMProvider
    
    providers = []
    for provider in llm_manager.get_available_providers():
        client = llm_manager.get_client(provider)
        providers.append({
            "provider": provider.value,
            "model": client.model,
            "is_default": provider == llm_manager._default_provider
        })
    
    return {
        "providers": providers,
        "default": llm_manager._default_provider.value if llm_manager._default_provider else None
    }


# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(avatars.router, prefix="/api/v1")
app.include_router(data_sources.router, prefix="/api/v1")
app.include_router(user_data.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(simulations.router, prefix="/api/v1")
app.include_router(sandbox.router, prefix="/api/v1")
app.include_router(counterfactual.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")

# 注册 WebSocket 路由（无需前缀）
app.include_router(websocket.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
