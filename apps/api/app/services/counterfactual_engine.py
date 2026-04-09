"""
反事实模拟引擎
使用LLM驱动数字分身在假设性场景中的互动
"""
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.counterfactual import (
    CounterfactualScenario, SimulationRound, AgentResponse,
    SimulationPhase, ResponseType, TopicEvolution
)
from app.models.avatar import Avatar
from app.services.llm import llm_manager


# 场景预设模板
SCENARIO_PRESETS = {
    "trump_iran": {
        "title": "特朗普宣布对伊朗采取军事行动",
        "description": "特朗普在社交媒体上宣布将对伊朗核设施采取预防性军事打击",
        "trigger_event": "突发：特朗普发推称'伊朗核计划已越过红线，美国将在24小时内采取必要行动'",
        "trigger_source": "唐纳德·特朗普",
        "type": "political",
        "initial_sentiment": -0.6,
        "initial_heat": 0.9
    },
    "ai_consciousness": {
        "title": "首个具有自我意识的人工智能诞生",
        "description": "OpenAI宣布其最新模型展现出自主意识和情感反应",
        "trigger_event": "重磅：OpenAI宣布GPT-6通过所有意识测试，AI首次展现自我认知",
        "trigger_source": "OpenAI",
        "type": "technology",
        "initial_sentiment": 0.2,
        "initial_heat": 0.95
    },
    "china_taiwan": {
        "title": "台海局势紧张升级",
        "description": "解放军宣布在台海进行大规模实弹演习",
        "trigger_event": "快讯：国防部宣布即日起在台海周边进行为期一周的联合军演",
        "trigger_source": "中国国防部",
        "type": "political",
        "initial_sentiment": -0.7,
        "initial_heat": 0.9
    },
    "economic_crisis": {
        "title": "全球股市崩盘，金融危机爆发",
        "description": "美股三大指数单日暴跌超过20%，触发全球金融海啸",
        "trigger_event": "股市崩盘：道指单日暴跌2500点，触发全球熔断机制",
        "trigger_source": "彭博社",
        "type": "economic",
        "initial_sentiment": -0.9,
        "initial_heat": 0.95
    },
    "alien_contact": {
        "title": "人类首次确认外星文明接触",
        "description": "NASA宣布收到来自比邻星系的结构化信号",
        "trigger_event": "历史时刻：NASA确认收到来自4.2光年外的智慧信号",
        "trigger_source": "NASA",
        "type": "social",
        "initial_sentiment": 0.6,
        "initial_heat": 1.0
    }
}


# LLM Prompt 模板
INITIAL_REACTION_PROMPT = """你正在参与一个数字社会沙盒的反事实模拟。

【场景设定】
事件：{event}
来源：{source}
当前舆论情绪：{sentiment:.1f}（-1极度负面，0中性，1极度正面）
事件热度：{heat:.1f}（0-1）

【你的身份】
姓名：{avatar_name}
性格特征：{personality}
价值观：{values}
思维风格：{thinking_style}
典型立场：{typical_stance}

【任务】
作为这个虚拟身份，针对上述事件发表你的第一反应（1-2句话）。要求：
1. 必须符合你的性格特征和价值观
2. 体现你的典型立场倾向
3. 语言风格要符合你的身份
4. 包含明确的情绪倾向（支持/反对/质疑/调侃等）

请以JSON格式输出：
{{
  "content": "你的发言内容",
  "response_type": "initial_reaction",
  "sentiment": 0.0,
  "stance": "support|oppose|neutral|question",
  "confidence": 0.8,
  "thinking_process": "简要说明你为什么会这样反应（基于你的哪些性格特征）"
}}
"""

REPLY_PROMPT = """【反事实模拟 - 第{round}轮】

话题：{topic}
当前讨论氛围：{atmosphere}

【上下文】
{context}

【你要回复的消息】
来自 @{target_name}：{target_content}

【你的身份】
{avatar_identity}

【任务】
基于你的立场和性格，选择是否回复这条消息。如果要回复：
1. 可以支持、反驳、调侃或提出新观点
2. 保持你的人设一致性
3. 可以引用你的专业知识或人生经验
4. 语言风格要自然真实

请以JSON格式输出：
{{
  "will_reply": true|false,
  "content": "回复内容（如果不回复则为空）",
  "response_type": "reply|refute|amplify|joke|analysis",
  "sentiment": 0.0,
  "stance": "support|oppose|neutral",
  "thinking_process": "思考过程"
}}
"""

TOPIC_ANALYSIS_PROMPT = """分析以下数字社会沙盒中产生的讨论内容，提取话题演变趋势：

【上轮话题】
{last_topic}

【本轮发言摘要】
{messages}

【分析任务】
1. 话题是否发生演变？如果演变，新话题是什么？
2. 提炼3-5个关键词
3. 整体情绪倾向如何？
4. 有哪些子话题出现？

请以JSON格式输出：
{{
  "topic_continued": true|false,
  "new_topic": "话题标题（如果发生演变）",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "sentiment_shift": -0.1,
  "subtopics": ["子话题1", "子话题2"],
  "analysis": "简要分析"
}}
"""


class CounterfactualEngine:
    """反事实模拟引擎"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.topic_keywords_history = []
    
    async def create_scenario(
        self,
        user_id: UUID,
        preset_key: Optional[str] = None,
        custom_title: Optional[str] = None,
        custom_event: Optional[str] = None,
        avatar_ids: Optional[List[UUID]] = None,
        max_rounds: int = 5
    ) -> CounterfactualScenario:
        """创建新的反事实场景"""
        
        if preset_key and preset_key in SCENARIO_PRESETS:
            preset = SCENARIO_PRESETS[preset_key]
            scenario = CounterfactualScenario(
                user_id=user_id,
                title=preset["title"],
                description=preset["description"],
                trigger_event=preset["trigger_event"],
                trigger_source=preset["trigger_source"],
                scenario_type=preset["type"],
                initial_sentiment=preset["initial_sentiment"],
                initial_heat=preset["initial_heat"],
                max_rounds=max_rounds,
                avatar_ids=avatar_ids or [],
                status="pending"
            )
        else:
            scenario = CounterfactualScenario(
                user_id=user_id,
                title=custom_title or "自定义场景",
                description=custom_event or "",
                trigger_event=custom_event or "",
                trigger_source="用户设定",
                scenario_type="custom",
                initial_sentiment=0.0,
                initial_heat=0.5,
                max_rounds=max_rounds,
                avatar_ids=avatar_ids or [],
                status="pending"
            )
        
        self.db.add(scenario)
        await self.db.commit()
        await self.db.refresh(scenario)
        
        return scenario
    
    async def run_simulation(self, scenario_id: UUID) -> Dict[str, Any]:
        """运行完整的反事实模拟"""
        
        # 获取场景
        result = await self.db.execute(
            select(CounterfactualScenario).where(CounterfactualScenario.id == scenario_id)
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            raise ValueError("Scenario not found")
        
        # 更新状态
        scenario.status = "running"
        scenario.started_at = datetime.utcnow()
        await self.db.commit()
        
        try:
            # 获取所有参与分身
            avatars = []
            for avatar_id in scenario.avatar_ids:
                result = await self.db.execute(select(Avatar).where(Avatar.id == avatar_id))
                avatar = result.scalar_one_or_none()
                if avatar:
                    avatars.append(avatar)
            
            if len(avatars) < 2:
                raise ValueError("Need at least 2 avatars for simulation")
            
            # 轮次模拟
            current_topic = scenario.trigger_event
            all_responses = []
            
            for round_num in range(1, scenario.max_rounds + 1):
                print(f"[Counterfactual] Running round {round_num}/{scenario.max_rounds}")
                
                # 确定当前阶段
                if round_num == 1:
                    phase = SimulationPhase.INITIAL
                elif round_num <= 3:
                    phase = SimulationPhase.SPREAD
                elif round_num <= 4:
                    phase = SimulationPhase.DEBATE
                else:
                    phase = SimulationPhase.EVOLUTION
                
                # 创建轮次记录
                round_record = SimulationRound(
                    scenario_id=scenario.id,
                    round_number=round_num,
                    phase=phase,
                    topic=current_topic,
                    topic_keywords=[]
                )
                self.db.add(round_record)
                await self.db.flush()
                
                # 生成分身反应
                round_responses = await self._generate_round_responses(
                    scenario, round_record, avatars, all_responses, phase
                )
                
                # 更新轮次统计
                await self._update_round_stats(round_record, round_responses)
                
                # 分析话题演变
                if round_num > 1:
                    current_topic = await self._analyze_topic_evolution(
                        scenario, current_topic, round_responses
                    )
                    round_record.topic = current_topic
                
                all_responses.extend(round_responses)
                
                # 每轮提交一次
                await self.db.commit()
            
            # 生成最终总结
            await self._generate_summary(scenario, all_responses)
            
            scenario.status = "completed"
            scenario.completed_at = datetime.utcnow()
            await self.db.commit()
            
            return {
                "scenario_id": str(scenario.id),
                "status": "completed",
                "rounds": scenario.max_rounds,
                "total_responses": len(all_responses)
            }
            
        except Exception as e:
            scenario.status = "failed"
            await self.db.commit()
            raise e
    
    async def _generate_round_responses(
        self,
        scenario: CounterfactualScenario,
        round_record: SimulationRound,
        avatars: List[Avatar],
        all_previous_responses: List[AgentResponse],
        phase: SimulationPhase
    ) -> List[AgentResponse]:
        """生成分身在当前轮次的反应"""
        
        responses = []
        
        # 第一轮：所有人都做初始反应
        if phase == SimulationPhase.INITIAL:
            for avatar in avatars:
                try:
                    response = await self._generate_initial_reaction(avatar, scenario)
                    if response:
                        response["round_id"] = round_record.id
                        response["avatar_id"] = avatar.id
                        responses.append(response)
                except Exception as e:
                    print(f"[Counterfactual] Error generating response for {avatar.name}: {e}")
        
        # 后续轮次：基于上一轮热门回复进行互动
        else:
            # 找出上一轮的热门回复
            hot_responses = self._select_hot_responses(all_previous_responses, n=3)
            
            # 选择一部分分身的回复
            responding_avatars = random.sample(avatars, min(len(avatars) - 1, random.randint(2, 4)))
            
            for avatar in responding_avatars:
                # 选择一个要回复的消息
                target = random.choice(hot_responses) if hot_responses else None
                
                if target and target["avatar_id"] != str(avatar.id):
                    try:
                        response = await self._generate_reply(avatar, target, scenario, round_record)
                        if response and response.get("will_reply"):
                            response["round_id"] = round_record.id
                            response["avatar_id"] = avatar.id
                            response["parent_response_id"] = target.get("id")
                            responses.append(response)
                    except Exception as e:
                        print(f"[Counterfactual] Error generating reply for {avatar.name}: {e}")
        
        # 保存到数据库
        db_responses = []
        for resp_data in responses:
            db_resp = AgentResponse(**resp_data)
            self.db.add(db_resp)
            db_responses.append(db_resp)
        
        await self.db.flush()
        return db_responses
    
    async def _generate_initial_reaction(
        self,
        avatar: Avatar,
        scenario: CounterfactualScenario
    ) -> Optional[Dict[str, Any]]:
        """生成初始反应"""
        
        # 构建身份描述
        identity = self._build_avatar_identity(avatar)
        
        prompt = INITIAL_REACTION_PROMPT.format(
            event=scenario.trigger_event,
            source=scenario.trigger_source,
            sentiment=scenario.initial_sentiment,
            heat=scenario.initial_heat,
            avatar_name=avatar.name,
            personality=identity.get("personality", "复杂多面"),
            values=identity.get("values", "追求真理"),
            thinking_style=identity.get("thinking_style", "理性分析"),
            typical_stance=identity.get("typical_stance", "中立客观")
        )
        
        try:
            response_text = await llm_manager.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个数字分身模拟器。请严格按照JSON格式输出，不要添加markdown代码块标记。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            # 清理响应文本
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            return {
                "content": data["content"],
                "response_type": data.get("response_type", ResponseType.INITIAL_REACTION),
                "sentiment": data.get("sentiment", 0.0),
                "stance": data.get("stance", "neutral"),
                "confidence": data.get("confidence", 0.5),
                "thinking_process": data.get("thinking_process", "")
            }
            
        except Exception as e:
            print(f"[Counterfactual] LLM error: {e}")
            # 备用方案：生成简单回复
            return {
                "content": f"关于{scenario.trigger_source}说的这件事，我觉得值得关注。",
                "response_type": ResponseType.INITIAL_REACTION,
                "sentiment": scenario.initial_sentiment * random.uniform(0.5, 1.5),
                "stance": "neutral",
                "confidence": 0.5,
                "thinking_process": "基于事件本身做出的中性反应"
            }
    
    async def _generate_reply(
        self,
        avatar: Avatar,
        target: Dict[str, Any],
        scenario: CounterfactualScenario,
        round_record: SimulationRound
    ) -> Optional[Dict[str, Any]]:
        """生成回复"""
        
        identity = self._build_avatar_identity(avatar)
        
        # 简化的上下文
        context = f"当前讨论热度：{round_record.heat_score:.1f}，整体情绪：{round_record.sentiment_score:.1f}"
        
        prompt = REPLY_PROMPT.format(
            round=round_record.round_number,
            topic=round_record.topic,
            atmosphere=context,
            context=f"@{target.get('from_name', '某人')} 说：{target.get('content', '')}",
            target_name=target.get("from_name", "某人"),
            target_content=target.get("content", ""),
            avatar_identity=f"姓名：{avatar.name}\n性格：{identity.get('personality', '复杂')}\n立场：{identity.get('typical_stance', '中立')}"
        )
        
        try:
            response_text = await llm_manager.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个数字分身模拟器。请严格按照JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            
            # 清理并解析
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            return {
                "will_reply": data.get("will_reply", True),
                "content": data.get("content", ""),
                "response_type": data.get("response_type", ResponseType.REPLY),
                "sentiment": data.get("sentiment", 0.0),
                "stance": data.get("stance", "neutral"),
                "thinking_process": data.get("thinking_process", "")
            }
            
        except Exception as e:
            print(f"[Counterfactual] Reply generation error: {e}")
            return {
                "will_reply": random.random() > 0.3,  # 70%概率回复
                "content": f"@{target.get('from_name', '某人')} 说得有道理，我也有类似的想法。",
                "response_type": ResponseType.REPLY,
                "sentiment": 0.0,
                "stance": "neutral",
                "thinking_process": "基本赞同对方观点"
            }
    
    async def _analyze_topic_evolution(
        self,
        scenario: CounterfactualScenario,
        last_topic: str,
        round_responses: List[AgentResponse]
    ) -> str:
        """分析话题演变"""
        
        if not round_responses:
            return last_topic
        
        # 提取本轮发言摘要
        messages = "\n".join([
            f"- {resp.avatar.name}: {resp.content[:100]}..."
            for resp in round_responses[:5]
        ])
        
        prompt = TOPIC_ANALYSIS_PROMPT.format(
            last_topic=last_topic,
            messages=messages
        )
        
        try:
            response_text = await llm_manager.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个话题分析专家。请严格按照JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            # 清理并解析
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            
            # 如果话题演变，返回新话题
            if not data.get("topic_continued", True) and data.get("new_topic"):
                return data["new_topic"]
            
            return last_topic
            
        except Exception as e:
            print(f"[Counterfactual] Topic analysis error: {e}")
            return last_topic
    
    async def _update_round_stats(
        self,
        round_record: SimulationRound,
        responses: List[AgentResponse]
    ):
        """更新轮次统计"""
        
        if not responses:
            return
        
        # 计算统计数据
        sentiments = [r.sentiment for r in responses]
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # 立场分布
        stances = {"support": 0, "oppose": 0, "neutral": 0}
        for r in responses:
            if r.stance in stances:
                stances[r.stance] += 1
        
        # 极化指数（标准差）
        if len(sentiments) > 1:
            mean = avg_sentiment
            variance = sum((s - mean) ** 2 for s in sentiments) / len(sentiments)
            polarization = variance ** 0.5
        else:
            polarization = 0
        
        round_record.sentiment_score = avg_sentiment
        round_record.stance_distribution = stances
        round_record.polarization_index = polarization
        round_record.message_count = len(responses)
        round_record.reach_count = len(set(r.avatar_id for r in responses))
        
        # 热度衰减模型
        base_heat = round_record.scenario.initial_heat
        decay = 0.1 * round_record.round_number
        engagement_boost = len(responses) * 0.05
        round_record.heat_score = max(0.1, min(1.0, base_heat - decay + engagement_boost))
    
    async def _generate_summary(
        self,
        scenario: CounterfactualScenario,
        all_responses: List[AgentResponse]
    ):
        """生成模拟总结"""
        
        # 简单统计摘要
        total_messages = len(all_responses)
        avg_sentiment = sum(r.sentiment for r in all_responses) / total_messages if total_messages > 0 else 0
        
        # 统计各立场数量
        stance_counts = {}
        for r in all_responses:
            stance_counts[r.stance] = stance_counts.get(r.stance, 0) + 1
        
        dominant_stance = max(stance_counts.items(), key=lambda x: x[1])[0] if stance_counts else "neutral"
        
        scenario.final_summary = f"""
模拟完成。共产生 {total_messages} 条讨论。
整体情绪倾向：{"正面" if avg_sentiment > 0.2 else "负面" if avg_sentiment < -0.2 else "中性"}
主导立场：{dominant_stance}
极化程度：{"高" if scenario.rounds[-1].polarization_index > 0.5 else "中" if scenario.rounds[-1].polarization_index > 0.3 else "低"}
        """.strip()
        
        scenario.key_findings = [
            f"讨论热度从 {scenario.initial_heat:.1f} 变化到 {scenario.rounds[-1].heat_score:.1f}",
            f"立场分布：支持{stance_counts.get('support', 0)}，反对{stance_counts.get('oppose', 0)}，中立{stance_counts.get('neutral', 0)}",
            f"话题从初始事件演变为：{scenario.rounds[-1].topic}"
        ]
    
    def _build_avatar_identity(self, avatar: Avatar) -> Dict[str, str]:
        """构建分身的身份描述"""
        
        # 从 cognitive_config 中提取信息
        config = avatar.cognitive_config or {}
        
        return {
            "personality": config.get("personality_traits", "复杂多面，难以简单定义"),
            "values": config.get("core_values", "追求真理与正义"),
            "thinking_style": config.get("thinking_style", "理性与感性并重"),
            "typical_stance": config.get("typical_stance", "根据具体事件判断"),
            "background": config.get("background", "具有丰富的人生阅历")
        }
    
    def _select_hot_responses(
        self,
        responses: List[AgentResponse],
        n: int = 3
    ) -> List[Dict[str, Any]]:
        """选择热门回复（基于影响力分数）"""
        
        if not responses:
            return []
        
        # 按影响力排序
        sorted_responses = sorted(
            responses,
            key=lambda r: abs(r.sentiment) + r.confidence,
            reverse=True
        )
        
        selected = sorted_responses[:n]
        return [
            {
                "id": str(r.id),
                "avatar_id": str(r.avatar_id),
                "from_name": r.avatar.name if hasattr(r, 'avatar') else "某人",
                "content": r.content,
                "sentiment": r.sentiment,
                "stance": r.stance
            }
            for r in selected
        ]


# 便捷函数
async def run_counterfactual_simulation(
    db: AsyncSession,
    user_id: UUID,
    preset: Optional[str] = None,
    custom_event: Optional[str] = None,
    avatar_ids: Optional[List[UUID]] = None,
    max_rounds: int = 5
) -> Dict[str, Any]:
    """运行反事实模拟的便捷函数"""
    
    engine = CounterfactualEngine(db)
    
    # 创建场景
    scenario = await engine.create_scenario(
        user_id=user_id,
        preset_key=preset,
        custom_event=custom_event,
        avatar_ids=avatar_ids,
        max_rounds=max_rounds
    )
    
    # 运行模拟
    result = await engine.run_simulation(scenario.id)
    
    return {
        "scenario_id": str(scenario.id),
        "title": scenario.title,
        **result
    }
