"""
社会模拟服务
"""
import random
import asyncio
from typing import Dict, Any, List, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.simulation import Simulation, ReactionType, SimulationStatus
from app.models.avatar import Avatar
from app.schemas.simulation import SimulationResult, VisualizationData, PropagationEvent


class EmotionalState:
    """情绪状态"""
    def __init__(self, pleasure: float = 0, arousal: float = 0, dominance: float = 0):
        self.pleasure = pleasure
        self.arousal = arousal
        self.dominance = dominance


class AvatarState:
    """模拟中的分身状态"""
    def __init__(self, avatar: Avatar):
        self.id = str(avatar.id)
        self.name = avatar.name
        self.influence = 5.0 + (avatar.interaction_count / 1000)  # 基础影响力
        self.emotion = EmotionalState()
        self.stance = {}  # 立场向量
        self.openness = 0.5
        self.susceptibility = 0.5
        self.reaction = "none"
        self.activation_step = -1


async def run_social_simulation(
    simulation: Simulation,
    db: AsyncSession,
    max_steps: int = 10
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """
    运行社会模拟
    
    Args:
        simulation: 模拟实例
        db: 数据库会话
        max_steps: 最大传播步数 (1-50)
    
    Returns:
        (result_data, visualization_data, thinking_processes)
    """
    # 限制步数范围
    max_steps = max(1, min(max_steps, 50))
    
    # 获取所有参与者
    avatar_states = {}
    for avatar_id in simulation.avatar_ids:
        result = await db.execute(select(Avatar).where(Avatar.id == avatar_id))
        avatar = result.scalar_one_or_none()
        if avatar:
            avatar_states[str(avatar.id)] = AvatarState(avatar)
    
    # 添加发起者
    initiator_id = str(simulation.initiator_avatar_id)
    if initiator_id not in avatar_states:
        result = await db.execute(select(Avatar).where(Avatar.id == simulation.initiator_avatar_id))
        avatar = result.scalar_one_or_none()
        if avatar:
            avatar_states[initiator_id] = AvatarState(avatar)
    
    # 模拟参数 - 使用传入的 max_steps
    max_iterations = max_steps
    activated: Set[str] = {initiator_id}
    newly_activated: Set[str] = {initiator_id}
    events: List[Dict] = []
    sentiment_timeline = [(0, 0.0)]
    
    # 设置发起者状态
    avatar_states[initiator_id].activation_step = 0
    avatar_states[initiator_id].reaction = "amplify"
    
    # 运行传播模拟
    for step in range(1, max_iterations + 1):
        if not newly_activated:
            break
        
        next_activated: Set[str] = set()
        step_sentiments = []
        
        for avatar_id in newly_activated:
            sender = avatar_states[avatar_id]
            
            # 模拟传播给未激活的节点
            for target_id, target in avatar_states.items():
                if target_id in activated or target_id == avatar_id:
                    continue
                
                # 计算传播概率
                prob = calculate_influence_probability(sender, target, simulation.initial_message)
                
                # 伯努利试验
                if random.random() < prob:
                    next_activated.add(target_id)
                    
                    # 确定反应类型
                    reaction = determine_reaction(sender, target)
                    target.reaction = reaction.value
                    target.activation_step = step
                    
                    # 情绪影响
                    emotional_impact = calculate_emotional_impact(sender, target, reaction)
                    target.emotion.pleasure += emotional_impact
                    target.emotion.pleasure = max(-1, min(1, target.emotion.pleasure))
                    step_sentiments.append(target.emotion.pleasure)
                    
                    # 记录事件
                    events.append({
                        "step": step,
                        "from_avatar_id": avatar_id,
                        "from_avatar_name": sender.name,
                        "to_avatar_id": target_id,
                        "to_avatar_name": target.name,
                        "reaction_type": reaction.value,
                        "influence_probability": prob
                    })
        
        # 更新激活集合：next_activated 是新发现的，需要从中筛选出真正新的
        newly_activated = next_activated - activated
        activated.update(next_activated)
        
        # 记录情感演变
        if step_sentiments:
            avg_sentiment = sum(step_sentiments) / len(step_sentiments)
            sentiment_timeline.append((step, avg_sentiment))
    
    # 计算统计结果
    reaction_counts = {}
    for state in avatar_states.values():
        reaction = state.reaction
        reaction_counts[reaction] = reaction_counts.get(reaction, 0) + 1
    
    # 识别关键影响者
    influencer_impact = {}
    for event in events:
        from_id = event["from_avatar_id"]
        influencer_impact[from_id] = influencer_impact.get(from_id, 0) + 1
    
    key_influencers = sorted(
        influencer_impact.keys(),
        key=lambda x: influencer_impact[x],
        reverse=True
    )
    
    # 计算极化程度
    stances = [s.emotion.pleasure for s in avatar_states.values() if s.activation_step > 0]
    polarization = calculate_polarization(stances) if stances else 0.0
    
    # 构建结果
    result_data = {
        "message_id": str(simulation.id),
        "content": simulation.initial_message[:100] + "...",
        "total_reach": len(activated),
        "propagation_steps": max([e["step"] for e in events]) if events else 0,
        "sentiment_evolution": sentiment_timeline,
        "key_influencers": key_influencers[:5],
        "reaction_distribution": reaction_counts,
        "polarization": polarization
    }
    
    # 构建可视化数据
    visualization_data = {
        "nodes": [
            {
                "id": state.id,
                "name": state.name,
                "influence": state.influence,
                "emotion": {
                    "pleasure": state.emotion.pleasure,
                    "arousal": state.emotion.arousal
                },
                "reaction": state.reaction,
                "activation_step": state.activation_step
            }
            for state in avatar_states.values()
        ],
        "edges": [
            {
                "source": e["from_avatar_id"],
                "target": e["to_avatar_id"],
                "step": e["step"],
                "probability": e["influence_probability"],
                "reaction": e["reaction_type"]
            }
            for e in events
        ],
        "timeline": sentiment_timeline,
        "stats": {
            "total_reach": len(activated),
            "max_depth": max([e["step"] for e in events]) if events else 0,
            "polarization": polarization
        }
    }
    
    # 生成思维过程数据
    thinking_processes: List[Dict[str, Any]] = []
    for event in events:
        step = event["step"]
        to_id = event["to_avatar_id"]
        to_name = event["to_avatar_name"]
        reaction = event["reaction_type"]
        
        # 生成思维内容
        thinking = generate_thinking_content(
            to_name, 
            simulation.initial_message, 
            reaction,
            event["influence_probability"]
        )
        
        thinking_processes.append({
            "step": step,
            "avatar_id": str(to_id),
            "avatar_name": to_name,
            "thinking": thinking
        })
    
    return result_data, visualization_data, thinking_processes


def calculate_influence_probability(
    sender: AvatarState,
    receiver: AvatarState,
    message: str
) -> float:
    """计算影响力传播概率"""
    base_prob = 0.15
    
    # 发送者影响力
    influence_factor = min(sender.influence / 10, 1.0) * 0.3
    
    # 接收者开放性
    openness_factor = receiver.openness * 0.2
    
    # 立场相似度（简化：随机）
    stance_similarity = random.uniform(0.3, 0.8)
    stance_factor = stance_similarity * 0.25
    
    # 综合计算
    probability = base_prob + influence_factor + openness_factor + stance_factor
    
    return min(max(probability, 0.01), 0.95)


def determine_reaction(sender: AvatarState, receiver: AvatarState) -> ReactionType:
    """确定反应类型"""
    # 基于立场相似度和随机因素
    stance_sim = random.uniform(0, 1)
    
    if stance_sim > 0.7:
        return ReactionType.AMPLIFY if random.random() > 0.5 else ReactionType.SUPPORT
    elif stance_sim > 0.5:
        return ReactionType.SUPPORT
    elif stance_sim > 0.3:
        return ReactionType.NEUTRAL
    elif stance_sim > 0.2:
        return ReactionType.QUESTION
    elif stance_sim > 0.1:
        return ReactionType.OPPOSE
    else:
        return ReactionType.IGNORE


def calculate_emotional_impact(
    sender: AvatarState,
    receiver: AvatarState,
    reaction: ReactionType
) -> float:
    """计算情绪影响"""
    reaction_emotions = {
        ReactionType.SUPPORT: 0.3,
        ReactionType.AMPLIFY: 0.5,
        ReactionType.NEUTRAL: 0.0,
        ReactionType.QUESTION: -0.1,
        ReactionType.OPPOSE: -0.4,
        ReactionType.IGNORE: 0.0
    }
    
    base_impact = reaction_emotions.get(reaction, 0.0)
    susceptibility = receiver.susceptibility
    
    return base_impact * susceptibility


def calculate_polarization(stance_values: List[float]) -> float:
    """计算社区极化程度"""
    if len(stance_values) < 2:
        return 0.0
    
    # 计算方差
    mean = sum(stance_values) / len(stance_values)
    variance = sum((x - mean) ** 2 for x in stance_values) / len(stance_values)
    
    return min(variance, 1.0)


def generate_thinking_content(
    avatar_name: str,
    message: str,
    reaction: str,
    probability: float
) -> str:
    """
    生成分身的思维过程
    
    这是一个简化版的思维生成，实际场景中可以使用 LLM 来生成更丰富的内容
    """
    message_preview = message[:50] + "..." if len(message) > 50 else message
    
    thinkings = {
        "support": [
            f"看到这条消息，我觉得很有道理。{message_preview} 这与我的想法不谋而合。",
            f"这个观点我认同，值得支持一下。",
            f"嗯，说得不错，{avatar_name}表示赞同。",
        ],
        "amplify": [
            f"这非常重要！大家一定要关注：{message_preview}",
            f"太对了！我必须让更多人看到这个观点。",
            f"这是一个关键问题，{avatar_name}认为需要大声疾呼！",
        ],
        "oppose": [
            f"这个观点我不同意，{message_preview} 太过片面了。",
            f"我觉得有问题，需要提出质疑。",
            f"{avatar_name}对此持保留态度，不太认同这个说法。",
        ],
        "question": [
            f"这个说法值得商榷，{avatar_name}想多了解一些细节。",
            f"有点疑问，这个消息的来源可靠吗？",
            f"{avatar_name}觉得需要更多证据来支持这个观点。",
        ],
        "neutral": [
            f"看到了这个消息，{avatar_name}选择保持中立。",
            f"这个观点还有待观察，暂不表态。",
            f"{avatar_name}认为这件事还需要更多信息才能判断。",
        ],
        "ignore": [
            f"这个消息看起来不太重要，{avatar_name}选择忽略。",
            f"不感兴趣，继续忙自己的事情。",
            f"{avatar_name}觉得这条消息不值得关注。",
        ],
    }
    
    import random
    reaction_key = reaction.lower() if reaction else "neutral"
    options = thinkings.get(reaction_key, thinkings["neutral"])
    return random.choice(options)
