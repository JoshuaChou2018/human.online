"""
社会模拟相关路由
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.avatar import Avatar
from app.models.simulation import Simulation, SimulationStatus
from app.schemas.simulation import (
    SimulationCreate, SimulationResponse, SimulationListResponse,
    SimulationResult, VisualizationData, SimulationStartRequest,
    CounterfactualRequest, CounterfactualResponse,
    SimulationStreamEvent, StreamEventType
)
from app.services.simulation import run_social_simulation
from app.services.llm import llm_manager

router = APIRouter(prefix="/simulations", tags=["社会模拟"])


@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    data: SimulationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的社会模拟"""
    # 验证所有参与者
    for avatar_id in data.avatar_ids:
        result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Avatar {avatar_id} not found"
            )
        
        if not avatar.is_public and avatar.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to use avatar {avatar_id}"
            )
    
    # 验证发起者
    result = await db.execute(select(Avatar).where(Avatar.id == data.initiator_avatar_id))
    initiator = result.scalar_one_or_none()
    
    if not initiator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Initiator avatar not found"
        )
    
    simulation = Simulation(
        name=data.name,
        description=data.description,
        user_id=current_user.id,
        initial_message=data.initial_message,
        initiator_avatar_id=data.initiator_avatar_id,
        avatar_ids=data.avatar_ids,
        max_steps=data.max_steps,
        status=SimulationStatus.PENDING
    )
    
    db.add(simulation)
    await db.commit()
    await db.refresh(simulation)
    
    return simulation


@router.get("", response_model=SimulationListResponse)
async def list_simulations(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模拟列表"""
    query = select(Simulation).where(Simulation.user_id == current_user.id)
    
    # 获取总数
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    # 分页
    query = query.order_by(Simulation.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模拟详情"""
    result = await db.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    simulation = result.scalar_one_or_none()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return simulation


@router.post("/{simulation_id}/start", response_model=dict)
async def start_simulation(
    simulation_id: UUID,
    data: SimulationStartRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """开始运行模拟"""
    result = await db.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    simulation = result.scalar_one_or_none()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if simulation.status == SimulationStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulation is already running"
        )
    
    # 更新状态
    simulation.status = SimulationStatus.RUNNING
    await db.commit()
    
    # 运行模拟
    try:
        # 优先使用请求中的 max_steps，否则使用模拟创建时的设置
        max_steps = data.max_steps if data else simulation.max_steps
        result_data, visualization_data, thinking_processes = await run_social_simulation(simulation, db, max_steps=max_steps)
        
        # 保存结果
        simulation.status = SimulationStatus.COMPLETED
        simulation.result = result_data
        simulation.visualization = visualization_data
        from datetime import datetime
        simulation.completed_at = datetime.utcnow()
        await db.commit()
        
        return {
            "status": "completed",
            "simulation_id": simulation_id,
            "result": result_data,
            "thinking_processes": thinking_processes
        }
    except Exception as e:
        simulation.status = SimulationStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}"
        )


@router.get("/{simulation_id}/results", response_model=dict)
async def get_simulation_results(
    simulation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模拟结果"""
    result = await db.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    simulation = result.scalar_one_or_none()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if simulation.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulation is not completed yet"
        )
    
    return {
        "simulation": {
            "id": simulation.id,
            "name": simulation.name,
            "status": simulation.status
        },
        "result": simulation.result,
        "visualization": simulation.visualization
    }


@router.delete("/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_simulation(
    simulation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模拟"""
    result = await db.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    simulation = result.scalar_one_or_none()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    await db.delete(simulation)
    await db.commit()
    
    return None


@router.post("/counterfactual", response_model=CounterfactualResponse)
async def run_counterfactual_simulation(
    data: CounterfactualRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    运行反事实模拟（沙盒模式）
    
    快速模拟多个AI角色之间的社交传播和对话
    """
    try:
        # 验证所有参与者avatar
        avatar_ids = data.avatar_ids
        
        if not avatar_ids:
            return CounterfactualResponse(
                success=False,
                error="至少需要选择一个参与者"
            )
        
        # 解析UUID
        try:
            uuid_ids = [UUID(aid) for aid in avatar_ids]
        except ValueError:
            return CounterfactualResponse(
                success=False,
                error="Invalid avatar ID format"
            )
        
        # 查找avatar
        from sqlalchemy import select as sa_select
        result = await db.execute(
            sa_select(Avatar).where(Avatar.id.in_(uuid_ids))
        )
        avatars = result.scalars().all()
        
        if len(avatars) != len(avatar_ids):
            return CounterfactualResponse(
                success=False,
                error="某些Avatar不存在或无权限访问"
            )
        
        # 验证权限
        for avatar in avatars:
            if not avatar.is_public and avatar.user_id != current_user.id:
                return CounterfactualResponse(
                    success=False,
                    error=f"没有权限使用Avatar: {avatar.name}"
                )
        
        # 确定内容
        content = data.custom_event or "开始模拟"
        
        # 确定发起者
        initiator_id = data.initiator_id
        if not initiator_id and avatar_ids:
            initiator_id = avatar_ids[0]
        
        # 场景配置
        scenario_configs = {
            "cyberpunk": {"name": "赛博朋克城市", "atmosphere": "高科技低生活"},
            "wuxia": {"name": "武侠江湖", "atmosphere": "快意恩仇"},
            "office": {"name": "现代职场", "atmosphere": "职场斗争"},
            "school": {"name": "校园", "atmosphere": "青春校园"},
            "custom": {"name": "自定义场景", "atmosphere": "自由发挥"}
        }
        
        scenario_config = scenario_configs.get(data.preset, scenario_configs.get("custom", {"name": "自定义场景", "atmosphere": "自由发挥"}))
        
        # 构建avatar信息
        avatar_info = []
        for avatar in avatars:
            avatar_info.append({
                "id": str(avatar.id),
                "name": avatar.name,
                "role": "参与者",
                "personality": [],
                "influence": 0.5
            })
        
        # 运行模拟
        simulation_result = await _run_quick_simulation(
            content=content,
            avatars=avatar_info,
            initiator_id=str(initiator_id),
            scenario=scenario_config,
            max_steps=data.max_steps,
            max_rounds=data.max_rounds
        )
        
        # 直接使用模拟结果（已经包含LLM生成的内容）
        response_data = {
            "id": simulation_result["simulation_id"],
            "scenario": simulation_result["scenario"],
            "nodes": simulation_result["visualization"]["nodes"],
            "edges": simulation_result["visualization"]["edges"],
            "timeline": simulation_result["visualization"]["timeline"],
            "stats": simulation_result["visualization"]["stats"],
            "messages": simulation_result["messages"],
            "max_steps": simulation_result["max_steps"],
            "max_rounds": simulation_result["max_rounds"],
            "created_at": simulation_result["created_at"]
        }
        
        return CounterfactualResponse(
            success=True,
            data=response_data
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return CounterfactualResponse(
            success=False,
            error=str(e)
        )


async def _generate_avatar_response(
    avatar_name: str,
    avatar_role: str,
    event_content: str,
    reaction_type: str,
    scenario: Dict,
    context: List[Dict] = None
) -> Dict[str, str]:
    """
    使用LLM生成分身的思考过程和发言
    
    Returns:
        {
            "thinking": "内心思考过程...",
            "message": "实际发言内容...",
            "sentiment": 0.5,  # -1 到 1
            "emotion_emoji": "😊"
        }
    """
    try:
        # 构建系统提示
        system_prompt = f"""你是数字分身{avatar_name}，一个AI驱动的虚拟人格。你正在参与一个关于"{scenario['name']}"的社会模拟。

场景氛围：{scenario['atmosphere']}
你的角色：{avatar_role}

你需要根据接收到的事件，生成：
1. 内心思考过程（thinking）- 用第一人称描述你的想法、顾虑、判断过程
2. 实际发言（message）- 你会对外说什么，要符合你的性格
3. 情感态度（用emoji表示）

反应类型：{reaction_type}（支持/反对/中立/放大/质疑）

请用JSON格式返回：
{{
    "thinking": "内心思考...",
    "message": "实际发言...",
    "sentiment": 0.5,
    "emotion_emoji": "😊"
}}"""

        # 构建用户提示
        user_prompt = f"""接收到的事件：{event_content}

请生成你的反应。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用LLM
        response = await llm_manager.chat_completion(
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )
        
        # 解析JSON响应
        import json
        try:
            # 尝试直接解析
            result = json.loads(response)
        except json.JSONDecodeError:
            # 尝试从markdown代码块中提取
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # 提取花括号内容
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("无法解析LLM响应")
        
        return {
            "thinking": result.get("thinking", f"{avatar_name}正在思考..."),
            "message": result.get("message", result.get("response", "...")),
            "sentiment": float(result.get("sentiment", 0)),
            "emotion_emoji": result.get("emotion_emoji", "😐")
        }
        
    except Exception as e:
        # 降级处理：返回简单的默认响应
        emotion_map = {
            "support": ("😊", 0.6, "这听起来是个好主意，我觉得应该支持。"),
            "oppose": ("😠", -0.6, "我不同意这个观点，这可能会带来问题。"),
            "neutral": ("😐", 0, "我需要更多信息才能做出判断。"),
            "amplify": ("🤩", 0.8, "这太棒了！我完全同意，大家快来支持！"),
            "question": ("🤔", 0, "这个想法很有意思，但我想知道更多细节...")
        }
        emoji, sentiment, default_msg = emotion_map.get(reaction_type, ("😐", 0, "让我想想..."))
        
        return {
            "thinking": f"{avatar_name}在考虑这个事件的影响...",
            "message": default_msg,
            "sentiment": sentiment,
            "emotion_emoji": emoji
        }


async def _run_quick_simulation(
    content: str,
    avatars: List[Dict],
    initiator_id: str,
    scenario: Dict,
    max_steps: int = 10,
    max_rounds: int = 3
) -> Dict:
    """
    快速运行反事实模拟（不保存到数据库），使用LLM生成真实对话
    """
    import random
    from datetime import datetime
    
    # 初始化avatar状态
    avatar_states = {}
    for avatar in avatars:
        avatar_states[avatar["id"]] = {
            "id": avatar["id"],
            "name": avatar["name"],
            "role": avatar.get("role", "参与者"),
            "influence": avatar.get("influence", 0.5),
            "openness": random.uniform(0.3, 0.8),
            "activated": False,
            "activation_step": -1,
            "emotion": {"valence": random.uniform(-0.3, 0.3), "arousal": random.uniform(0.3, 0.7)},
            "responses": []  # 存储该avatar的所有响应
        }
    
    # 传播模拟
    events = []
    messages = []  # LLM生成的消息
    activated = {initiator_id}
    newly_activated = {initiator_id}
    avatar_states[initiator_id]["activated"] = True
    avatar_states[initiator_id]["activation_step"] = 0
    
    # 生成初始事件的LLM响应（发起人）
    try:
        initiator = avatar_states[initiator_id]
        initial_response = await _generate_avatar_response(
            avatar_name=initiator["name"],
            avatar_role=initiator["role"],
            event_content=content,
            reaction_type="initiate",
            scenario=scenario
        )
    except:
        initial_response = {
            "thinking": f"{initiator['name']}发起这个话题",
            "message": content,
            "sentiment": 0,
            "emotion_emoji": "📢"
        }
    
    # 记录初始事件
    events.append({
        "step": 0,
        "round": 1,
        "from_avatar_id": initiator_id,
        "from_name": initiator["name"],
        "to_avatar_id": initiator_id,
        "to_name": initiator["name"],
        "reaction_type": "initiate",
        "reaction_content": initial_response["message"],
        "probability": 1.0,
        "thinking": initial_response["thinking"],
        "emotion_emoji": initial_response["emotion_emoji"]
    })
    
    messages.append({
        "id": f"msg_init",
        "avatar_id": initiator_id,
        "avatar_name": initiator["name"],
        "content": initial_response["message"],
        "thinking": initial_response["thinking"],
        "step": 0,
        "round": 1,
        "response_type": "initiate",
        "sentiment": initial_response["sentiment"],
        "stance": "neutral",
        "emotion_emoji": initial_response["emotion_emoji"]
    })
    
    # 传播算法
    max_iterations = max(1, min(max_steps, 50))
    
    for step in range(1, max_iterations + 1):
        if not newly_activated:
            break
        
        next_activated = set()
        
        for avatar_id in newly_activated:
            sender = avatar_states[avatar_id]
            
            for target_id, target in avatar_states.items():
                if target_id in activated or target_id == avatar_id:
                    continue
                
                # 计算影响概率
                base_prob = sender["influence"] * (1 - abs(target["openness"] - 0.5))
                prob = min(0.9, max(0.05, base_prob))
                
                if random.random() < prob:
                    next_activated.add(target_id)
                    target["activated"] = True
                    target["activation_step"] = step
                    
                    # 决定反应类型
                    reaction_types = ["support", "oppose", "neutral", "amplify", "question"]
                    reaction_weights = [0.3, 0.2, 0.2, 0.15, 0.15]
                    reaction = random.choices(reaction_types, weights=reaction_weights)[0]
                    
                    # 使用LLM生成响应
                    # 构建上下文（之前的发言）
                    context = [m for m in messages if m["step"] < step]
                    context_text = "\n".join([f"{m['avatar_name']}: {m['content']}" for m in context[-3:]])
                    
                    event_context = f"{content}\n\n之前的讨论：\n{context_text}" if context_text else content
                    
                    try:
                        llm_response = await _generate_avatar_response(
                            avatar_name=target["name"],
                            avatar_role=target["role"],
                            event_content=event_context,
                            reaction_type=reaction,
                            scenario=scenario
                        )
                        reaction_content = llm_response["message"]
                        thinking = llm_response["thinking"]
                        sentiment = llm_response["sentiment"]
                        emotion_emoji = llm_response["emotion_emoji"]
                    except Exception as e:
                        # 降级到默认响应
                        reaction_content = f"{target['name']}对消息做出了{reaction}反应"
                        thinking = f"{target['name']}在思考这个事件..."
                        sentiment = 0
                        emotion_emoji = "😐"
                    
                    # 根据LLM返回的情感值确定立场，而不是随机的reaction_type
                    if sentiment > 0.2:
                        stance = "support"
                    elif sentiment < -0.2:
                        stance = "oppose"
                    else:
                        stance = "neutral"
                    
                    events.append({
                        "step": step,
                        "round": 1,
                        "from_avatar_id": avatar_id,
                        "from_name": sender["name"],
                        "to_avatar_id": target_id,
                        "to_name": target["name"],
                        "reaction_type": reaction,
                        "reaction_content": reaction_content,
                        "probability": prob,
                        "thinking": thinking,
                        "emotion_emoji": emotion_emoji
                    })
                    
                    messages.append({
                        "id": f"msg_{step}_{target_id}",
                        "avatar_id": target_id,
                        "avatar_name": target["name"],
                        "content": reaction_content,
                        "thinking": thinking,
                        "step": step,
                        "round": 1,
                        "response_type": reaction,
                        "sentiment": sentiment,
                        "stance": stance,
                        "emotion_emoji": emotion_emoji
                    })
        
        # 修复：在更新 activated 之前计算 newly_activated
        newly_activated = next_activated - activated
        activated.update(next_activated)
    
    # 构建可视化数据
    nodes = []
    for avatar_id, state in avatar_states.items():
        # 获取该avatar的最新情绪
        avatar_msgs = [m for m in messages if m["avatar_id"] == avatar_id]
        latest_sentiment = avatar_msgs[-1]["sentiment"] if avatar_msgs else 0
        latest_emoji = avatar_msgs[-1]["emotion_emoji"] if avatar_msgs else "😐"
        
        nodes.append({
            "id": avatar_id,
            "name": state["name"],
            "influence": state["influence"],
            "emotion": {
                "valence": latest_sentiment,
                "arousal": state["emotion"]["arousal"],
                "emoji": latest_emoji
            },
            "reaction": "activated" if state["activated"] else "inactive",
            "activation_step": state["activation_step"]
        })
    
    edges = []
    for event in events:
        if event["step"] > 0:
            edges.append({
                "source": event["from_avatar_id"],
                "target": event["to_avatar_id"],
                "step": event["step"],
                "probability": event["probability"],
                "reaction": event["reaction_type"]
            })
    
    # 统计数据
    total_activated = len([n for n in nodes if n["activation_step"] >= 0])
    sentiment_evolution = []
    for step in range(max_iterations + 1):
        step_messages = [m for m in messages if m["step"] == step]
        if step_messages:
            avg_sentiment = sum(m["sentiment"] for m in step_messages) / len(step_messages)
            sentiment_evolution.append((step, avg_sentiment))
    
    reaction_dist = {}
    for event in events:
        rt = event["reaction_type"]
        reaction_dist[rt] = reaction_dist.get(rt, 0) + 1
    
    # 计算平均情绪作为极化指标
    all_sentiments = [m["sentiment"] for m in messages]
    avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0
    polarization = abs(avg_sentiment) if all_sentiments else 0
    
    # 模拟结果
    return {
        "simulation_id": f"cf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
        "scenario": scenario,
        "events": events,
        "messages": messages,
        "visualization": {
            "nodes": nodes,
            "edges": edges,
            "timeline": sentiment_evolution,
            "stats": {
                "total_reach": total_activated,
                "propagation_steps": max([e["step"] for e in events]) if events else 0,
                "max_depth": max([e["step"] for e in events]) if events else 0,
                "total_events": len(events),
                "total_messages": len(messages),
                "reaction_distribution": reaction_dist,
                "polarization": polarization
            }
        },
        "max_steps": max_steps,
        "max_rounds": max_rounds,
        "created_at": datetime.now().isoformat()
    }


# ============================================
# 流式实时模拟
# ============================================

async def _run_streaming_simulation(
    content: str,
    avatars: List[Dict],
    initiator_id: str,
    scenario: Dict,
    max_steps: int = 10,
    max_rounds: int = 3
):
    """
    流式运行反事实模拟，实时产生事件
    """
    import random
    import json
    from datetime import datetime
    
    simulation_id = f"cf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
    
    def make_event(event_type: StreamEventType, step: int, round_num: int, data: Dict) -> str:
        """创建SSE事件"""
        event = {
            "type": event_type.value,
            "step": step,
            "round": round_num,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"
    
    # 发送开始事件
    yield make_event(StreamEventType.START, 0, 1, {
        "simulation_id": simulation_id,
        "scenario": scenario,
        "total_avatars": len(avatars),
        "max_steps": max_steps
    })
    await asyncio.sleep(0.01)  # 强制刷新缓冲区
    
    # 初始化avatar状态
    avatar_states = {}
    for avatar in avatars:
        avatar_states[avatar["id"]] = {
            "id": avatar["id"],
            "name": avatar["name"],
            "role": avatar.get("role", "参与者"),
            "influence": avatar.get("influence", 0.5),
            "openness": random.uniform(0.3, 0.8),
            "activated": False,
            "activation_step": -1,
            "emotion": {"valence": random.uniform(-0.3, 0.3), "arousal": random.uniform(0.3, 0.7)},
        }
    
    # 传播模拟
    events = []
    messages = []
    activated = {initiator_id}
    newly_activated = {initiator_id}
    avatar_states[initiator_id]["activated"] = True
    avatar_states[initiator_id]["activation_step"] = 0
    
    # 发送发起人激活事件
    initiator = avatar_states[initiator_id]
    yield make_event(StreamEventType.NODE_ACTIVATE, 0, 1, {
        "avatar_id": initiator_id,
        "avatar_name": initiator["name"],
        "step": 0,
        "is_initiator": True
    })
    await asyncio.sleep(0.01)  # 强制刷新缓冲区
    
    # 生成初始响应
    try:
        initial_response = await _generate_avatar_response(
            avatar_name=initiator["name"],
            avatar_role=initiator["role"],
            event_content=content,
            reaction_type="initiate",
            scenario=scenario
        )
    except:
        initial_response = {
            "thinking": f"{initiator['name']}发起这个话题",
            "message": content,
            "sentiment": 0,
            "emotion_emoji": "📢"
        }
    
    # 发送初始消息事件
    yield make_event(StreamEventType.MESSAGE, 0, 1, {
        "id": f"msg_init",
        "avatar_id": initiator_id,
        "avatar_name": initiator["name"],
        "content": initial_response["message"],
        "thinking": initial_response["thinking"],
        "response_type": "initiate",
        "sentiment": initial_response["sentiment"],
        "stance": "neutral",
        "emotion_emoji": initial_response["emotion_emoji"]
    })
    await asyncio.sleep(0.01)  # 强制刷新缓冲区
    
    messages.append({
        "id": f"msg_init",
        "avatar_id": initiator_id,
        "avatar_name": initiator["name"],
        "content": initial_response["message"],
        "thinking": initial_response["thinking"],
        "step": 0,
        "round": 1,
        "response_type": "initiate",
        "sentiment": initial_response["sentiment"],
        "stance": "neutral",
        "emotion_emoji": initial_response["emotion_emoji"]
    })
    
    # 传播算法
    max_iterations = max(1, min(max_steps, 50))
    
    for step in range(1, max_iterations + 1):
        if not newly_activated:
            break
        
        next_activated = set()
        
        for avatar_id in newly_activated:
            sender = avatar_states[avatar_id]
            
            for target_id, target in avatar_states.items():
                if target_id in activated or target_id == avatar_id:
                    continue
                
                # 计算影响概率
                base_prob = sender["influence"] * (1 - abs(target["openness"] - 0.5))
                prob = min(0.9, max(0.05, base_prob))
                
                if random.random() < prob:
                    next_activated.add(target_id)
                    target["activated"] = True
                    target["activation_step"] = step
                    
                    # 发送节点激活事件
                    yield make_event(StreamEventType.NODE_ACTIVATE, step, 1, {
                        "avatar_id": target_id,
                        "avatar_name": target["name"],
                        "step": step,
                        "from_avatar_id": avatar_id,
                        "from_name": sender["name"],
                        "probability": prob
                    })
                    await asyncio.sleep(0.01)  # 强制刷新缓冲区
                    
                    # 决定反应类型
                    reaction_types = ["support", "oppose", "neutral", "amplify", "question"]
                    reaction_weights = [0.3, 0.2, 0.2, 0.15, 0.15]
                    reaction = random.choices(reaction_types, weights=reaction_weights)[0]
                    
                    # 构建上下文
                    context = [m for m in messages if m["step"] < step]
                    context_text = "\n".join([f"{m['avatar_name']}: {m['content']}" for m in context[-3:]])
                    event_context = f"{content}\n\n之前的讨论：\n{context_text}" if context_text else content
                    
                    # 发送思考中事件
                    yield make_event(StreamEventType.THINKING, step, 1, {
                        "avatar_id": target_id,
                        "avatar_name": target["name"],
                        "status": "generating"
                    })
                    await asyncio.sleep(0.01)  # 强制刷新缓冲区
                    
                    # 使用LLM生成响应
                    try:
                        llm_response = await _generate_avatar_response(
                            avatar_name=target["name"],
                            avatar_role=target["role"],
                            event_content=event_context,
                            reaction_type=reaction,
                            scenario=scenario
                        )
                    except Exception as e:
                        llm_response = {
                            "thinking": f"{target['name']}在思考...",
                            "message": f"{target['name']}做出了回应",
                            "sentiment": 0,
                            "emotion_emoji": "😐"
                        }
                    
                    # 根据LLM返回的情感值确定立场，而不是随机的reaction_type
                    sentiment = llm_response["sentiment"]
                    if sentiment > 0.2:
                        stance = "support"
                    elif sentiment < -0.2:
                        stance = "oppose"
                    else:
                        stance = "neutral"
                    
                    # 发送消息事件
                    msg_data = {
                        "id": f"msg_{step}_{target_id}",
                        "avatar_id": target_id,
                        "avatar_name": target["name"],
                        "content": llm_response["message"],
                        "thinking": llm_response["thinking"],
                        "step": step,
                        "round": 1,
                        "response_type": reaction,
                        "sentiment": llm_response["sentiment"],
                        "stance": stance,
                        "emotion_emoji": llm_response["emotion_emoji"],
                        "from_avatar_id": avatar_id,
                        "from_name": sender["name"]
                    }
                    yield make_event(StreamEventType.MESSAGE, step, 1, msg_data)
                    await asyncio.sleep(0.01)  # 强制刷新缓冲区
                    
                    messages.append(msg_data)
                    
                    # 发送边创建事件
                    yield make_event(StreamEventType.EDGE_CREATE, step, 1, {
                        "source": avatar_id,
                        "target": target_id,
                        "step": step,
                        "probability": prob,
                        "reaction": reaction
                    })
                    await asyncio.sleep(0.01)  # 强制刷新缓冲区
                    
                    # 小延迟让用户能看到过程
                    await asyncio.sleep(0.5)
        
        # 更新激活集合
        newly_activated = next_activated - activated
        activated.update(next_activated)
        
        # 发送步骤完成事件
        if step < max_iterations:
            yield make_event(StreamEventType.STEP_COMPLETE, step, 1, {
                "activated_count": len(activated),
                "new_activations": len(newly_activated)
            })
            await asyncio.sleep(0.01)  # 强制刷新缓冲区
    
    # 构建最终统计
    nodes = []
    for avatar_id, state in avatar_states.items():
        avatar_msgs = [m for m in messages if m["avatar_id"] == avatar_id]
        latest_sentiment = avatar_msgs[-1]["sentiment"] if avatar_msgs else 0
        latest_emoji = avatar_msgs[-1]["emotion_emoji"] if avatar_msgs else "😐"
        
        nodes.append({
            "id": avatar_id,
            "name": state["name"],
            "influence": state["influence"],
            "emotion": {
                "valence": latest_sentiment,
                "arousal": state["emotion"]["arousal"],
                "emoji": latest_emoji
            },
            "reaction": "activated" if state["activated"] else "inactive",
            "activation_step": state["activation_step"]
        })
    
    edges = []
    for event in events:
        if event.get("step", 0) > 0:
            edges.append({
                "source": event.get("from_avatar_id"),
                "target": event.get("to_avatar_id"),
                "step": event.get("step"),
                "probability": event.get("probability", 0),
                "reaction": event.get("reaction_type")
            })
    
    # 发送完成事件
    yield make_event(StreamEventType.COMPLETE, max_iterations, 1, {
        "simulation_id": simulation_id,
        "nodes": nodes,
        "edges": edges,
        "messages": messages,
        "stats": {
            "total_reach": len(activated),
            "total_messages": len(messages)
        }
    })
    await asyncio.sleep(0.01)  # 强制刷新缓冲区


@router.post("/counterfactual/stream")
async def run_counterfactual_stream(
    data: CounterfactualRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    流式运行反事实模拟（实时显示）
    
    使用 SSE (Server-Sent Events) 实时返回模拟过程中的每一步
    """
    try:
        # 验证所有参与者avatar
        avatar_ids = data.avatar_ids
        
        if not avatar_ids:
            return StreamingResponse(
                iter([f"data: {json.dumps({'type': 'error', 'error': '至少需要选择一个参与者'})}\n\n"]),
                media_type="text/event-stream"
            )
        
        # 解析UUID
        try:
            uuid_ids = [UUID(aid) for aid in avatar_ids]
        except ValueError:
            return StreamingResponse(
                iter([f"data: {json.dumps({'type': 'error', 'error': 'Invalid avatar ID format'})}\n\n"]),
                media_type="text/event-stream"
            )
        
        # 查找avatar
        from sqlalchemy import select as sa_select
        result = await db.execute(
            sa_select(Avatar).where(Avatar.id.in_(uuid_ids))
        )
        avatars = result.scalars().all()
        
        if len(avatars) != len(avatar_ids):
            return StreamingResponse(
                iter([f"data: {json.dumps({'type': 'error', 'error': '某些Avatar不存在或无权限访问'})}\n\n"]),
                media_type="text/event-stream"
            )
        
        # 验证权限
        for avatar in avatars:
            if not avatar.is_public and avatar.user_id != current_user.id:
                return StreamingResponse(
                    iter([f"data: {json.dumps({'type': 'error', 'error': f'没有权限使用Avatar: {avatar.name}'})}\n\n"]),
                    media_type="text/event-stream"
                )
        
        # 确定内容
        content = data.custom_event or "开始模拟"
        
        # 确定发起者
        initiator_id = data.initiator_id
        if not initiator_id and avatar_ids:
            initiator_id = avatar_ids[0]
        
        # 场景配置
        scenario_configs = {
            "cyberpunk": {"name": "赛博朋克城市", "atmosphere": "高科技低生活"},
            "wuxia": {"name": "武侠江湖", "atmosphere": "快意恩仇"},
            "office": {"name": "现代职场", "atmosphere": "职场斗争"},
            "school": {"name": "校园", "atmosphere": "青春校园"},
            "custom": {"name": "自定义场景", "atmosphere": "自由发挥"}
        }
        
        scenario_config = scenario_configs.get(data.preset, scenario_configs.get("custom", {"name": "自定义场景", "atmosphere": "自由发挥"}))
        
        # 构建avatar信息
        avatar_info = []
        for avatar in avatars:
            avatar_info.append({
                "id": str(avatar.id),
                "name": avatar.name,
                "role": "参与者",
                "personality": [],
                "influence": 0.5
            })
        
        # 返回流式响应 - 禁用所有缓冲
        return StreamingResponse(
            _run_streaming_simulation(
                content=content,
                avatars=avatar_info,
                initiator_id=str(initiator_id),
                scenario=scenario_config,
                max_steps=data.max_steps,
                max_rounds=data.max_rounds
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Content-Type-Options": "nosniff",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"]),
            media_type="text/event-stream"
        )
