"""
应用配置
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "Human.online API"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/humanonline"
    MONGODB_URL: str = "mongodb://localhost:27017/humanonline"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 向量数据库配置
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "humanonline"
    
    # ============================================
    # LLM 配置 - 支持多模型
    # ============================================
    
    # 默认使用的 LLM 提供商 (openai | kimi | anthropic)
    DEFAULT_LLM_PROVIDER: str = "openai"
    
    # --- OpenAI 配置 ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # --- Kimi (Moonshot) 配置 ---
    KIMI_API_KEY: Optional[str] = None
    KIMI_API_ID: Optional[str] = None  # 中国特别版可能需要 API ID
    KIMI_MODEL: str = "moonshot-v1-32k"  # 可选: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
    
    # --- Kimi Code 配置 ---
    KIMICODE_API_KEY: Optional[str] = None
    KIMICODE_BASE_URL: Optional[str] = None  # 例如: https://api.xxx.com/v1
    KIMICODE_MODEL: str = "kimi-code"
    
    # --- DeepSeek 配置 ---
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"  # 可选: deepseek-chat, deepseek-coder, deepseek-reasoner
    
    # --- Anthropic (Claude) 配置 ---
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    # --- Azure OpenAI 配置 ---
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_MODEL: str = "gpt-4"
    
    # ============================================
    # 安全配置
    # ============================================
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    ALGORITHM: str = "HS256"
    
    # Google OAuth 配置
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    
    # CORS 配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://humind.life",
        "https://humind.life",
    ]
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "/tmp/humanonline/uploads"
    
    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def check_llm_config():
    """检查 LLM 配置是否有效"""
    has_openai = bool(settings.OPENAI_API_KEY)
    has_kimi = bool(settings.KIMI_API_KEY)
    has_anthropic = bool(settings.ANTHROPIC_API_KEY)
    
    if not any([has_openai, has_kimi, has_anthropic]):
        print("⚠️  Warning: No LLM API keys configured!")
        print("   Please set at least one of:")
        print("   - OPENAI_API_KEY")
        print("   - KIMI_API_KEY")
        print("   - ANTHROPIC_API_KEY")
        return False
    
    # 检查默认提供商是否可用
    default = settings.DEFAULT_LLM_PROVIDER.lower()
    provider_map = {
        "openai": has_openai,
        "kimi": has_kimi,
        "anthropic": has_anthropic,
    }
    
    if default in provider_map and not provider_map[default]:
        available = [k for k, v in provider_map.items() if v]
        if available:
            print(f"⚠️  Warning: Default provider '{default}' is not configured.")
            print(f"   Available providers: {', '.join(available)}")
            print(f"   Please update DEFAULT_LLM_PROVIDER or configure {default.upper()}_API_KEY")
            return False
    
    return True
