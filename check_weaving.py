#!/usr/bin/env python3
"""
编织故障排查脚本
用于检查 MindWeave 编织过程中的问题
"""

import asyncio
import sys
sys.path.insert(0, 'apps/api')

async def check_weaving_status(avatar_id: str):
    """检查指定分身的编织状态"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.avatar import Avatar
    from app.models.weaving_progress import WeavingProgress
    
    async with AsyncSessionLocal() as db:
        # 检查分身
        result = await db.execute(
            select(Avatar).where(Avatar.id == avatar_id)
        )
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            print(f"❌ 未找到分身: {avatar_id}")
            return
        
        print(f"👤 分身信息:")
        print(f"   ID: {avatar.id}")
        print(f"   名称: {avatar.name}")
        print(f"   状态: {avatar.status}")
        print(f"   公开: {avatar.is_public}")
        
        # 检查进度
        result = await db.execute(
            select(WeavingProgress).where(WeavingProgress.avatar_id == avatar_id)
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            print(f"
⚠️ 未找到编织进度记录！这意味着编织任务可能没有正确启动。")
            return
        
        print(f"
📊 编织进度:")
        print(f"   当前阶段: {progress.current_stage}")
        print(f"   总体进度: {progress.overall_progress}%")
        print(f"   错误信息: {progress.error_message or '无'}")
        print(f"   日志数量: {len(progress.logs) if progress.logs else 0}")
        
        if progress.logs:
            print(f"
📝 最近日志:")
            for log in progress.logs[-10:]:  # 最近 10 条
                print(f"   [{log.get('timestamp', 'N/A')}] {log.get('type', 'info')}: {log.get('message', '')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python check_weaving.py <avatar_id>")
        print("例子: python check_weaving.py 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)
    
    avatar_id = sys.argv[1]
    asyncio.run(check_weaving_status(avatar_id))
