"""
沙盒实时模拟 API
支持流式输出，实时显示分身之间的互动
"""
import json
import random
import asyncio
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import Enum

from app.core.database import get_db
from app.auth import get_current_user
from app.auth.jwt import verify_token
from app.models.user import User
from app.models.avatar import Avatar, AvatarStatus
from app.models.simulation import SandboxMember
from app.services.llm import llm_manager, LLMProvider
from fastapi import Query, Request
from sqlalchemy import select as sa_select

router = APIRouter(prefix="/sandbox", tags=["沙盒实时模拟"])


async def get_current_user_from_token(
    request: Request,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """从 URL 参数或 Header 获取当前用户"""
    # 首先尝试从 URL 参数获取 token
    auth_token = token
    
    # 如果没有，尝试从 Header 获取
    if not auth_token:
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    # 验证 token
    payload = verify_token(auth_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # 查询用户
    result = await db.execute(sa_select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


class StreamEventType(str, Enum):
    """流式事件类型"""
    START = "start"
    NODE_ACTIVATE = "node_activate"
    MESSAGE = "message"
    THINKING = "thinking"
    RELATION_UPDATE = "relation_update"
    TOPIC_CHANGE = "topic_change"
    ROUND_END = "round_end"
    COMPLETE = "complete"
    ERROR = "error"


async def generate_sandbox_activity(
    avatar: Avatar,
    context: str,
    topic: str
) -> Dict:
    """
    使用 LLM 生成沙盒中的分身活动
    """
    system_prompt = f"""你是 {avatar.name}，一个基于 MindWeave 技术构建的数字分身。

你的特征：
{avatar.system_prompt or '你是一个有独特认知特征的AI分身'}

当前场景：沙盒社会模拟
当前话题：{topic}
上下文：{context}

请生成一个自然的行为，可以是：
1. 发表观点（speaking）
2. 内心思考（thinking）
3. 对他人做出反应（reacting）

以 JSON 格式返回：
{{
    "action": "speaking|thinking|reacting",
    "content": "具体内容",
    "thinking": "思维过程（50字以内）",
    "emotion": "positive|neutral|negative|excited",
    "topic": "相关话题标签"
}}
"""

    try:
        client = llm_manager.get_client()
        response = await client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请基于当前话题'{topic}'生成一个自然的行为"}
            ],
            temperature=0.8,
            max_tokens=300
        )
        
        # 解析 JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "action": data.get("action", "speaking"),
                "content": data.get("content", response[:100]),
                "thinking": data.get("thinking", ""),
                "emotion": data.get("emotion", "neutral"),
                "topic": data.get("topic", topic)
            }
    except Exception as e:
        print(f"[Sandbox] Error generating activity for {avatar.name}: {e}")
    
    # 默认返回
    return {
        "action": random.choice(["speaking", "thinking", "reacting"]),
        "content": f"{avatar.name}正在思考...",
        "thinking": "这是一个模拟的思维过程",
        "emotion": random.choice(["positive", "neutral", "negative", "excited"]),
        "topic": topic
    }


async def run_sandbox_stream(
    avatars: List[Avatar],
    initial_topic: str,
    max_rounds: int = 5,
    delay_between_events: float = 2.0
) -> AsyncGenerator[str, None]:
    """
    流式运行沙盒模拟
    """
    simulation_id = f"sandbox_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
    
    def make_event(event_type: StreamEventType, data: Dict) -> str:
        event = {
            "type": event_type.value,
            "simulation_id": simulation_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"
    
    # 发送开始事件
    yield make_event(StreamEventType.START, {
        "total_avatars": len(avatars),
        "initial_topic": initial_topic,
        "max_rounds": max_rounds,
        "avatars": [{"id": str(a.id), "name": a.name} for a in avatars]
    })
    
    # 激活所有分身
    for i, avatar in enumerate(avatars):
        yield make_event(StreamEventType.NODE_ACTIVATE, {
            "avatar_id": str(avatar.id),
            "avatar_name": avatar.name,
            "step": i,
            "color": f"hsl({(i * 60) % 360}, 70%, 50%)"
        })
        await asyncio.sleep(0.3)
    
    # 当前话题
    current_topic = initial_topic
    recent_messages = []
    
    # 模拟多轮互动
    for round_num in range(1, max_rounds + 1):
        yield make_event(StreamEventType.ROUND_END, {
            "round": round_num,
            "total_rounds": max_rounds,
            "topic": current_topic
        })
        
        # 每轮随机选择2-3个分身发言
        active_avatars = random.sample(avatars, min(random.randint(2, 3), len(avatars)))
        
        for avatar in active_avatars:
            # 构建上下文
            context = " | ".join(recent_messages[-3:]) if recent_messages else "对话刚开始"
            
            # 生成活动
            activity = await generate_sandbox_activity(avatar, context, current_topic)
            
            # 发送思维事件
            if activity["thinking"]:
                yield make_event(StreamEventType.THINKING, {
                    "avatar_id": str(avatar.id),
                    "avatar_name": avatar.name,
                    "thinking": activity["thinking"]
                })
                await asyncio.sleep(0.5)
            
            # 发送消息/活动事件
            yield make_event(StreamEventType.MESSAGE, {
                "avatar_id": str(avatar.id),
                "avatar_name": avatar.name,
                "action": activity["action"],
                "content": activity["content"],
                "emotion": activity["emotion"],
                "topic": activity["topic"],
                "round": round_num
            })
            
            # 更新最近消息
            recent_messages.append(f"{avatar.name}: {activity['content'][:50]}")
            
            # 偶尔更换话题
            if random.random() < 0.2 and activity["topic"] != current_topic:
                old_topic = current_topic
                current_topic = activity["topic"]
                yield make_event(StreamEventType.TOPIC_CHANGE, {
                    "from": old_topic,
                    "to": current_topic,
                    "triggered_by": avatar.name
                })
            
            await asyncio.sleep(delay_between_events)
        
        # 随机更新关系
        if len(avatars) >= 2 and random.random() < 0.3:
            a1, a2 = random.sample(avatars, 2)
            yield make_event(StreamEventType.RELATION_UPDATE, {
                "from": str(a1.id),
                "from_name": a1.name,
                "to": str(a2.id),
                "to_name": a2.name,
                "relation": random.choice(["agree", "disagree", "curious", "neutral"]),
                "strength": random.uniform(0.3, 1.0)
            })
    
    # 发送完成事件
    yield make_event(StreamEventType.COMPLETE, {
        "total_rounds": max_rounds,
        "final_topic": current_topic,
        "message_count": len(recent_messages)
    })


@router.get("/stream")
async def start_sandbox_simulation(
    topic: str = "日常闲聊",
    max_rounds: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    启动沙盒实时模拟（流式）
    
    使用 SSE 实时返回分身之间的互动
    """
    try:
        # 获取沙盒中的活跃分身
        result = await db.execute(
            select(SandboxMember)
            .where(SandboxMember.status == "active")
        )
        sandbox_members = result.scalars().all()
        
        # 获取对应的 Avatar
        avatar_ids = [m.avatar_id for m in sandbox_members]
        if not avatar_ids:
            # 如果没有沙盒成员，使用所有公开就绪的分身
            result = await db.execute(
                select(Avatar)
                .where(
                    Avatar.is_public == True,
                    Avatar.status == AvatarStatus.READY
                )
                .limit(5)
            )
            avatars = result.scalars().all()
        else:
            result = await db.execute(
                select(Avatar)
                .where(Avatar.id.in_(avatar_ids))
            )
            avatars = result.scalars().all()
        
        if len(avatars) < 2:
            return StreamingResponse(
                iter([f"data: {json.dumps({'type': 'error', 'error': '沙盒中需要至少2个分身才能开始模拟'})}\n\n"]),
                media_type="text/event-stream"
            )
        
        # 返回流式响应
        return StreamingResponse(
            run_sandbox_stream(
                avatars=list(avatars),
                initial_topic=topic,
                max_rounds=max_rounds,
                delay_between_events=2.0
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"]),
            media_type="text/event-stream"
        )
