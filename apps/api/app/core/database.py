"""
数据库连接管理
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from typing import AsyncGenerator

from app.core.config import settings

# SQLAlchemy 配置
Base = declarative_base()

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool if settings.DEBUG else None,
    future=True,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# MongoDB 客户端
mongodb_client: AsyncIOMotorClient = None

# Redis 客户端
redis_client: redis.Redis = None


async def init_mongodb():
    """初始化 MongoDB 连接"""
    global mongodb_client
    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    return mongodb_client


async def close_mongodb():
    """关闭 MongoDB 连接"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()


async def init_redis():
    """初始化 Redis 连接"""
    global redis_client
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖函数"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_mongodb():
    """获取 MongoDB 数据库实例"""
    return mongodb_client[settings.MONGODB_URL.split('/')[-1]]


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端"""
    return redis_client


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
