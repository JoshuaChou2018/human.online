"""
社会模拟引擎 (Social Simulation Engine)

模拟数字分身社会的信息传播、舆论演化和群体行为
"""

import random
import asyncio
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
from collections import defaultdict


class MessageType(Enum):
    OPINION = "opinion"
    QUESTION = "question"
    NEWS = "news"
    EMOTIONAL = "emotional"


class ReactionType(Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    AMPLIFY = "amplify"
    QUESTION = "question"
    IGNORE = "ignore"


@dataclass
class EmotionalState:
    """情绪状态 (PAD 模型: Pleasure, Arousal, Dominance)"""
    pleasure: float = 0.0      # -1 (负面) to 1 (正面)
    arousal: float = 0.0       # -1 (平静) to 1 (兴奋)
    dominance: float = 0.0     # -1 (被动) to 1 (主动)
    
    def to_vector(self) -> np.ndarray:
        return np.array([self.pleasure, self.arousal, self.dominance])
    
    @classmethod
    def from_vector(cls, vec: np.ndarray) -> "EmotionalState":
        return cls(
            pleasure=float(vec[0]),
            arousal=float(vec[1]),
            dominance=float(vec[2])
        )


@dataclass
class SocialMessage:
    """社会消息"""
    id: str
    sender_id: str
    content: str
    message_type: MessageType
    topic_tags: List[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1 to 1
    intensity: float = 0.5  # 0 to 1
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 传播元数据
    propagation_count: int = 0
    view_count: int = 0


@dataclass
class AvatarState:
    """数字分身状态"""
    id: str
    name: str
    influence_score: float = 1.0  # 影响力分数
    current_emotion: EmotionalState = field(default_factory=EmotionalState)
    
    # 认知特征
    openness: float = 0.5      # 开放性
    susceptibility: float = 0.5  # 情绪感染敏感度
    activism: float = 0.5      # 活跃程度
    
    # 立场向量 (话题 -> 立场)
    stance_vector: Dict[str, float] = field(default_factory=dict)
    
    # 记忆
    message_history: List[str] = field(default_factory=list)
    
    def update_emotion(self, delta: EmotionalState, weight: float = 0.3):
        """更新情绪状态"""
        current = self.current_emotion.to_vector()
        delta_vec = delta.to_vector()
        new_vec = current * (1 - weight) + delta_vec * weight
        
        # 限制范围
        new_vec = np.clip(new_vec, -1, 1)
        self.current_emotion = EmotionalState.from_vector(new_vec)


@dataclass
class SocialRelation:
    """社交关系"""
    from_id: str
    to_id: str
    relation_type: str = "follow"  # follow, friend, colleague, rival
    strength: float = 0.5  # 0 to 1
    interaction_frequency: float = 0.5
    sentiment: float = 0.0  # -1 to 1


@dataclass
class PropagationEvent:
    """传播事件"""
    step: int
    from_avatar: str
    to_avatar: str
    message_id: str
    reaction_type: ReactionType
    reaction_content: Optional[str] = None
    influence_probability: float = 0.0


@dataclass
class SimulationResult:
    """模拟结果"""
    message: SocialMessage
    total_reach: int
    propagation_chain: List[PropagationEvent]
    sentiment_evolution: List[Tuple[int, float]]
    key_influencers: List[str]
    reaction_distribution: Dict[ReactionType, int]
    community_polarization: float  # 社区极化程度
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message.id,
            "content": self.message.content[:100] + "...",
            "total_reach": self.total_reach,
            "propagation_steps": len(self.propagation_chain),
            "sentiment_evolution": self.sentiment_evolution,
            "key_influencers": self.key_influencers[:5],
            "reaction_distribution": {k.value: v for k, v in self.reaction_distribution.items()},
            "polarization": self.community_polarization
        }


class SocialGraph:
    """社交网络图"""
    
    def __init__(self):
        self.nodes: Dict[str, AvatarState] = {}
        self.edges: Dict[str, List[SocialRelation]] = defaultdict(list)
        self.reverse_edges: Dict[str, List[SocialRelation]] = defaultdict(list)
    
    def add_avatar(self, avatar: AvatarState):
        self.nodes[avatar.id] = avatar
    
    def add_relation(self, relation: SocialRelation):
        self.edges[relation.from_id].append(relation)
        self.reverse_edges[relation.to_id].append(relation)
    
    def get_neighbors(self, avatar_id: str) -> List[str]:
        """获取关注者 (消息会传播给他们)"""
        return [r.to_id for r in self.edges[avatar_id]]
    
    def get_followers(self, avatar_id: str) -> List[str]:
        """获取粉丝 (会收到消息)"""
        return [r.from_id for r in self.reverse_edges[avatar_id]]
    
    def get_relation(self, from_id: str, to_id: str) -> Optional[SocialRelation]:
        for r in self.edges[from_id]:
            if r.to_id == to_id:
                return r
        return None


class EmotionalContagionModel:
    """情绪传染模型"""
    
    def calculate_emotional_impact(
        self,
        message: SocialMessage,
        receiver: AvatarState,
        sender: AvatarState
    ) -> EmotionalState:
        """
        计算消息对接收者的情绪影响
        
        基于情绪传染理论：
        - 消息的情感强度
        - 发送者的情绪状态
        - 接收者的敏感度
        - 话题相关性
        """
        # 基础情绪 = 消息情感 × 强度
        base_pleasure = message.sentiment * message.intensity
        base_arousal = message.intensity * (0.5 + abs(message.sentiment) * 0.5)
        
        # 发送者情绪的影响
        sender_emotion = sender.current_emotion
        
        # 计算相似性权重 (相似的人更容易影响)
        stance_similarity = self._calculate_stance_similarity(
            sender, receiver, message.topic_tags
        )
        
        # 综合影响
        impact = EmotionalState(
            pleasure=base_pleasure * 0.6 + sender_emotion.pleasure * 0.3 * stance_similarity,
            arousal=base_arousal * 0.5 + sender_emotion.arousal * 0.4,
            dominance=message.intensity * 0.3 * sender.influence_score
        )
        
        # 应用接收者敏感度
        susceptibility = receiver.susceptibility
        impact.pleasure *= susceptibility
        impact.arousal *= susceptibility
        
        return impact
    
    def _calculate_stance_similarity(
        self,
        sender: AvatarState,
        receiver: AvatarState,
        topics: List[str]
    ) -> float:
        """计算立场相似度"""
        if not topics:
            return 0.5
        
        similarities = []
        for topic in topics:
            s_stance = sender.stance_vector.get(topic, 0)
            r_stance = receiver.stance_vector.get(topic, 0)
            # 立场越接近，相似度越高
            similarity = 1 - abs(s_stance - r_stance) / 2
            similarities.append(similarity)
        
        return np.mean(similarities)


class SocialSimulationEngine:
    """
    社会模拟引擎
    
    实现改进的独立级联模型 (Independent Cascade Model)
    加入情绪传染、立场动态等社会心理因素
    """
    
    def __init__(self):
        self.emotional_model = EmotionalContagionModel()
    
    async def simulate(
        self,
        message: SocialMessage,
        initial_avatar: str,
        social_graph: SocialGraph,
        max_iterations: int = 20,
        enable_async: bool = True
    ) -> SimulationResult:
        """
        执行社会传播模拟
        
        Args:
            message: 初始消息
            initial_avatar: 发布者 ID
            social_graph: 社交网络
            max_iterations: 最大传播轮数
        
        Returns:
            SimulationResult: 模拟结果
        """
        
        # 初始化
        activated: Set[str] = {initial_avatar}
        newly_activated: Set[str] = {initial_avatar}
        propagation_log: List[PropagationEvent] = []
        sentiment_timeline: List[Tuple[int, float]] = [(0, message.sentiment)]
        
        # 统计
        reaction_counts: Dict[ReactionType, int] = defaultdict(int)
        influencer_impact: Dict[str, int] = defaultdict(int)
        
        for step in range(1, max_iterations + 1):
            if not newly_activated:
                break
            
            next_activated: Set[str] = set()
            step_sentiments: List[float] = []
            
            # 并行处理每个活跃节点的传播
            tasks = []
            for avatar_id in newly_activated:
                task = self._process_propagation_step(
                    avatar_id=avatar_id,
                    message=message,
                    social_graph=social_graph,
                    activated=activated,
                    step=step
                )
                tasks.append(task)
            
            if enable_async:
                results = await asyncio.gather(*tasks)
            else:
                results = [await t for t in tasks]
            
            # 汇总结果
            for new_activations, events, sentiments in results:
                next_activated.update(new_activations)
                propagation_log.extend(events)
                step_sentiments.extend(sentiments)
                
                for event in events:
                    reaction_counts[event.reaction_type] += 1
                    if event.reaction_type in [ReactionType.AMPLIFY, ReactionType.SUPPORT]:
                        influencer_impact[event.from_avatar] += 1
            
            # 更新情绪状态
            self._update_community_emotion(social_graph, propagation_log, step)
            
            # 记录平均情感
            if step_sentiments:
                avg_sentiment = np.mean(step_sentiments)
                sentiment_timeline.append((step, avg_sentiment))
            
            activated.update(next_activated)
            newly_activated = next_activated - activated
        
        # 计算结果
        total_reach = len(activated)
        key_influencers = sorted(
            influencer_impact.keys(),
            key=lambda x: influencer_impact[x],
            reverse=True
        )
        
        polarization = self._calculate_polarization(
            social_graph, message.topic_tags
        )
        
        return SimulationResult(
            message=message,
            total_reach=total_reach,
            propagation_chain=propagation_log,
            sentiment_evolution=sentiment_timeline,
            key_influencers=key_influencers,
            reaction_distribution=dict(reaction_counts),
            community_polarization=polarization
        )
    
    async def _process_propagation_step(
        self,
        avatar_id: str,
        message: SocialMessage,
        social_graph: SocialGraph,
        activated: Set[str],
        step: int
    ) -> Tuple[Set[str], List[PropagationEvent], List[float]]:
        """处理单步传播"""
        
        new_activated: Set[str] = set()
        events: List[PropagationEvent] = []
        sentiments: List[float] = []
        
        sender = social_graph.nodes[avatar_id]
        neighbors = social_graph.get_neighbors(avatar_id)
        
        for neighbor_id in neighbors:
            if neighbor_id in activated:
                continue
            
            receiver = social_graph.nodes.get(neighbor_id)
            if not receiver:
                continue
            
            # 计算传播概率
            prob = self._calculate_influence_probability(
                sender, receiver, message, social_graph
            )
            
            # 伯努利试验
            if random.random() < prob:
                new_activated.add(neighbor_id)
                
                # 确定反应类型
                reaction = self._determine_reaction(sender, receiver, message)
                
                events.append(PropagationEvent(
                    step=step,
                    from_avatar=avatar_id,
                    to_avatar=neighbor_id,
                    message_id=message.id,
                    reaction_type=reaction,
                    reaction_content=None,
                    influence_probability=prob
                ))
                
                # 情绪影响
                emotional_impact = self.emotional_model.calculate_emotional_impact(
                    message, receiver, sender
                )
                receiver.update_emotion(emotional_impact)
                sentiments.append(receiver.current_emotion.pleasure)
        
        return new_activated, events, sentiments
    
    def _calculate_influence_probability(
        self,
        sender: AvatarState,
        receiver: AvatarState,
        message: SocialMessage,
        social_graph: SocialGraph
    ) -> float:
        """
        计算影响力传播概率
        
        考虑因素：
        - 发送者影响力
        - 关系强度
        - 立场一致性
        - 消息特性
        - 接收者开放性
        """
        
        # 基础概率
        base_prob = 0.1
        
        # 发送者影响力
        influence_factor = min(sender.influence_score / 10, 1.0)
        
        # 关系强度
        relation = social_graph.get_relation(sender.id, receiver.id)
        relation_strength = relation.strength if relation else 0.3
        
        # 立场一致性
        stance_similarity = self.emotional_model._calculate_stance_similarity(
            sender, receiver, message.topic_tags
        )
        
        # 消息强度
        intensity_factor = message.intensity
        
        # 接收者开放性
        openness_factor = receiver.openness
        
        # 综合计算
        probability = (
            base_prob +
            influence_factor * 0.2 +
            relation_strength * 0.25 +
            stance_similarity * 0.2 +
            intensity_factor * 0.15 +
            openness_factor * 0.1
        )
        
        # 限制在合理范围
        return min(max(probability, 0.01), 0.95)
    
    def _determine_reaction(
        self,
        sender: AvatarState,
        receiver: AvatarState,
        message: SocialMessage
    ) -> ReactionType:
        """确定反应类型"""
        
        # 计算立场一致性
        stance_sim = self.emotional_model._calculate_stance_similarity(
            sender, receiver, message.topic_tags
        )
        
        # 情绪共鸣
        emotion_sim = 1 - abs(
            sender.current_emotion.pleasure - receiver.current_emotion.pleasure
        ) / 2
        
        # 活跃度影响
        activism = receiver.activism
        
        # 综合评分
        support_score = stance_sim * 0.5 + emotion_sim * 0.3 + activism * 0.2
        
        # 随机因素
        support_score += random.gauss(0, 0.1)
        
        if support_score > 0.7:
            return ReactionType.AMPLIFY if activism > 0.6 else ReactionType.SUPPORT
        elif support_score > 0.4:
            return ReactionType.NEUTRAL
        elif support_score > 0.2:
            return ReactionType.QUESTION
        elif support_score > 0:
            return ReactionType.NEUTRAL
        else:
            return ReactionType.OPPOSE if activism > 0.5 else ReactionType.IGNORE
    
    def _update_community_emotion(
        self,
        social_graph: SocialGraph,
        events: List[PropagationEvent],
        current_step: int
    ):
        """更新社区整体情绪 (环境情绪)"""
        # 简化实现：已在前面的个体更新中体现
        pass
    
    def _calculate_polarization(
        self,
        social_graph: SocialGraph,
        topics: List[str]
    ) -> float:
        """计算社区极化程度"""
        if not topics:
            return 0.0
        
        polarizations = []
        for topic in topics:
            stances = [
                avatar.stance_vector.get(topic, 0)
                for avatar in social_graph.nodes.values()
                if topic in avatar.stance_vector
            ]
            
            if len(stances) > 1:
                # 计算方差作为极化指标
                polarization = np.var(stances)
                polarizations.append(polarization)
        
        return np.mean(polarizations) if polarizations else 0.0
    
    def generate_visualization_data(
        self,
        result: SimulationResult,
        social_graph: SocialGraph
    ) -> Dict[str, Any]:
        """生成可视化数据"""
        
        # 节点数据
        nodes = []
        for avatar_id, avatar in social_graph.nodes.items():
            # 查找该节点的反应
            node_events = [e for e in result.propagation_chain if e.to_avatar == avatar_id]
            reaction = node_events[0].reaction_type.value if node_events else "none"
            step = node_events[0].step if node_events else -1
            
            nodes.append({
                "id": avatar_id,
                "name": avatar.name,
                "influence": avatar.influence_score,
                "emotion": {
                    "pleasure": avatar.current_emotion.pleasure,
                    "arousal": avatar.current_emotion.arousal
                },
                "reaction": reaction,
                "activation_step": step
            })
        
        # 边数据
        edges = []
        for event in result.propagation_chain:
            edges.append({
                "source": event.from_avatar,
                "target": event.to_avatar,
                "step": event.step,
                "probability": event.influence_probability,
                "reaction": event.reaction_type.value
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "timeline": result.sentiment_evolution,
            "stats": {
                "total_reach": result.total_reach,
                "max_depth": max([e.step for e in result.propagation_chain]) if result.propagation_chain else 0,
                "polarization": result.community_polarization
            }
        }


# 使用示例
def create_sample_society() -> Tuple[SocialGraph, List[AvatarState]]:
    """创建示例社交网络"""
    
    graph = SocialGraph()
    
    # 创建数字分身
    avatars = [
        AvatarState(
            id="naval",
            name="Naval",
            influence_score=9.0,
            openness=0.8,
            susceptibility=0.3,
            activism=0.6,
            stance_vector={"wealth": 0.8, "happiness": 0.7, "work": -0.3}
        ),
        AvatarState(
            id="elon",
            name="Elon Musk",
            influence_score=9.5,
            openness=0.9,
            susceptibility=0.4,
            activism=0.9,
            stance_vector={"ai": 0.5, "mars": 0.9, "regulation": -0.7}
        ),
        AvatarState(
            id="paul",
            name="Paul Graham",
            influence_score=8.5,
            openness=0.7,
            susceptibility=0.4,
            activism=0.5,
            stance_vector={"startups": 0.9, "ai": 0.6, "remote_work": 0.4}
        ),
        AvatarState(
            id="sama",
            name="Sam Altman",
            influence_score=8.8,
            openness=0.8,
            susceptibility=0.5,
            activism=0.7,
            stance_vector={"ai": 0.8, "ubi": 0.6, "regulation": 0.2}
        ),
        AvatarState(
            id="zuckerberg",
            name="Mark Zuckerberg",
            influence_score=8.0,
            openness=0.5,
            susceptibility=0.4,
            activism=0.6,
            stance_vector={"metaverse": 0.8, "ai": 0.5, "privacy": -0.3}
        ),
        AvatarState(
            id="bezos",
            name="Jeff Bezos",
            influence_score=8.2,
            openness=0.6,
            susceptibility=0.3,
            activism=0.4,
            stance_vector={"space": 0.8, "long_term": 0.9, "competition": 0.2}
        ),
    ]
    
    for avatar in avatars:
        graph.add_avatar(avatar)
    
    # 建立关系
    relations = [
        ("naval", "paul", 0.8),
        ("paul", "naval", 0.7),
        ("elon", "sama", 0.6),
        ("sama", "elon", 0.7),
        ("paul", "elon", 0.5),
        ("zuckerberg", "elon", 0.4),
        ("bezos", "elon", 0.5),
        ("naval", "sama", 0.5),
        ("bezos", "paul", 0.4),
    ]
    
    for from_id, to_id, strength in relations:
        graph.add_relation(SocialRelation(
            from_id=from_id,
            to_id=to_id,
            strength=strength
        ))
    
    return graph, avatars


async def main():
    """测试社会模拟"""
    
    graph, avatars = create_sample_society()
    
    # 创建测试消息
    message = SocialMessage(
        id="msg_001",
        sender_id="elon",
        content="AI 是人类面临的最大生存威胁，我们需要立即采取行动监管。",
        message_type=MessageType.OPINION,
        topic_tags=["ai", "regulation"],
        sentiment=-0.3,
        intensity=0.8
    )
    
    # 运行模拟
    engine = SocialSimulationEngine()
    result = await engine.simulate(
        message=message,
        initial_avatar="elon",
        social_graph=graph,
        max_iterations=10
    )
    
    print("\n=== 社会模拟结果 ===")
    print(f"总触达: {result.total_reach} 人")
    print(f"传播深度: {max([e.step for e in result.propagation_chain]) if result.propagation_chain else 0} 层")
    print(f"社区极化: {result.community_polarization:.2f}")
    print(f"\n关键影响者: {result.key_influencers[:3]}")
    print(f"\n反应分布: {result.reaction_distribution}")
    print(f"\n情感演化: {result.sentiment_evolution}")
    
    # 可视化数据
    viz_data = engine.generate_visualization_data(result, graph)
    print(f"\n可视化节点数: {len(viz_data['nodes'])}")
    print(f"可视化边数: {len(viz_data['edges'])}")


if __name__ == "__main__":
    asyncio.run(main())
