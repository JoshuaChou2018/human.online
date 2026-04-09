#!/usr/bin/env python3
"""应用数据库迁移"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


async def apply_migration():
    """应用 max_steps 迁移"""
    async with engine.begin() as conn:
        # 检查列是否存在
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'simulations' AND column_name = 'max_steps'
        """))
        
        if result.scalar() is None:
            print("Adding max_steps column to simulations table...")
            await conn.execute(text("""
                ALTER TABLE simulations 
                ADD COLUMN max_steps INTEGER DEFAULT 10
            """))
            await conn.execute(text("""
                UPDATE simulations 
                SET max_steps = 10 
                WHERE max_steps IS NULL
            """))
            print("Migration applied successfully!")
        else:
            print("Column max_steps already exists, skipping migration.")


if __name__ == "__main__":
    asyncio.run(apply_migration())
