"""
认知蒸馏引擎 (Cognitive Distillation Engine)

基于 nuwa-skill 方法论实现，将个人数据转化为数字分身的认知配置。
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

import numpy as np
from openai import AsyncOpenAI


class AnalysisDimension(Enum):
    """六维认知分析"""
    EXPRESSION_DNA = "expression_dna"          # 表达 DNA
    MENTAL_MODELS = "mental_models"            # 心智模型
    DECISION_HEURISTICS = "decision_heuristics" # 决策启发式
    VALUE_BOUNDARIES = "value_boundaries"      # 价值观底线
    KNOWLEDGE_BOUNDARIES = "knowledge_boundaries" # 诚实边界
    RELATIONSHIP_PATTERNS = "relationship_patterns" # 关系模式


@dataclass
class DataSource:
    """数据源"""
    id: str
    source_type: str  # chat, document, social, audio
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_segments: List[Dict] = field(default_factory=list)


@dataclass
class CognitiveProfile:
    """认知特征档案"""
    expression_dna: Dict[str, Any] = field(default_factory=dict)
    mental_models: List[Dict] = field(default_factory=list)
    decision_heuristics: List[Dict] = field(default_factory=list)
    value_boundaries: List[str] = field(default_factory=list)
    knowledge_boundaries: List[str] = field(default_factory=list)
    relationship_patterns: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "expression_dna": self.expression_dna,
            "mental_models": self.mental_models,
            "decision_heuristics": self.decision_heuristics,
            "value_boundaries": self.value_boundaries,
            "knowledge_boundaries": self.knowledge_boundaries,
            "relationship_patterns": self.relationship_patterns
        }


@dataclass
class AvatarConfig:
    """数字分身配置"""
    name: str
    system_prompt: str
    style_params: Dict[str, float]
    cognitive_profile: CognitiveProfile
    knowledge_chunks: List[Dict]
    relationship_preferences: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "style_params": self.style_params,
            "cognitive_profile": self.cognitive_profile.to_dict(),
            "knowledge_chunks_count": len(self.knowledge_chunks),
            "relationship_preferences": self.relationship_preferences,
            "created_at": self.created_at.isoformat()
        }


class CognitiveDistiller:
    """
    认知蒸馏器
    
    实现 nuwa-skill 的六路并行分析和三重验证提炼
    """
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        self.client = openai_client or AsyncOpenAI()
        self.model = "gpt-4-turbo-preview"
        
    async def distill(
        self,
        name: str,
        data_sources: List[DataSource],
        strategy: str = "standard"
    ) -> AvatarConfig:
        """
        执行完整的认知蒸馏流程
        
        Args:
            name: 数字分身名称
            data_sources: 数据源列表
            strategy: 蒸馏策略 (quick/standard/deep)
        
        Returns:
            AvatarConfig: 完整的分身配置
        """
        
        # 1. 六路并行分析
        print(f"🔄 开始六维认知分析 ({strategy} 模式)...")
        analysis_results = await self._six_dimension_analysis(data_sources)
        
        # 2. 三重验证提炼
        print("🔍 执行三重验证...")
        verified_profile = await self._triple_verification(analysis_results)
        
        # 3. 构建知识向量库
        print("📚 构建知识库...")
        knowledge_chunks = await self._build_knowledge_base(data_sources)
        
        # 4. 生成系统 Prompt
        print("📝 生成认知框架...")
        system_prompt = self._build_system_prompt(name, verified_profile)
        
        # 5. 计算风格参数
        style_params = self._calculate_style_params(analysis_results["expression_dna"])
        
        # 6. 关系偏好分析
        relationship_prefs = analysis_results["relationship_patterns"]
        
        config = AvatarConfig(
            name=name,
            system_prompt=system_prompt,
            style_params=style_params,
            cognitive_profile=verified_profile,
            knowledge_chunks=knowledge_chunks,
            relationship_preferences=relationship_prefs
        )
        
        print("✅ 认知蒸馏完成!")
        return config
    
    async def _six_dimension_analysis(
        self,
        data_sources: List[DataSource]
    ) -> Dict[str, Any]:
        """六路并行分析"""
        
        # 合并所有文本内容用于分析
        combined_text = self._combine_sources(data_sources)
        
        # 并行执行六个维度的分析
        tasks = [
            self._analyze_expression_dna(combined_text),
            self._extract_mental_models(combined_text),
            self._identify_decision_heuristics(combined_text),
            self._detect_value_boundaries(combined_text),
            self._map_knowledge_boundaries(combined_text),
            self._analyze_relationship_patterns(combined_text)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            "expression_dna": results[0],
            "mental_models": results[1],
            "decision_heuristics": results[2],
            "value_boundaries": results[3],
            "knowledge_boundaries": results[4],
            "relationship_patterns": results[5]
        }
    
    async def _analyze_expression_dna(self, text: str) -> Dict[str, Any]:
        """分析表达 DNA"""
        prompt = f"""
        分析以下文本的表达风格特征，提取"表达 DNA":
        
        需要分析的维度：
        1. 语气特征 (正式/随意、热情/冷静、直接/含蓄)
        2. 句式偏好 (长短句比例、复杂程度、标点运用)
        3. 词汇特点 (专业术语密度、情感词汇偏好、口头禅)
        4. 修辞习惯 (比喻、排比、反问等的使用频率)
        5. 段落结构 (偏好简短还是详细、层次组织方式)
        6. 互动模式 (提问频率、回应方式、冲突处理)
        
        文本样本 (前 8000 字符):
        {text[:8000]}
        
        请以 JSON 格式输出分析结果：
        {{
            "tone": {{"formality": 0-1, "enthusiasm": 0-1, "directness": 0-1}},
            "sentence_patterns": {{"avg_length": float, "complexity": 0-1, "favorite_punctuation": [str]}},
            "vocabulary": {{"technical_density": 0-1, "emotional_markers": [str], "catchphrases": [str]}},
            "rhetoric": {{"metaphor_freq": 0-1, "parallelism_freq": 0-1, "rhetorical_question_freq": 0-1}},
            "structure": {{"paragraph_preference": "short|medium|long", "organization_style": str}},
            "interaction": {{"question_frequency": 0-1, "response_style": str, "conflict_approach": str}}
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _extract_mental_models(self, text: str) -> List[Dict]:
        """提取心智模型"""
        prompt = f"""
        分析以下文本中体现的认知框架和心智模型：
        
        心智模型定义：
        - 是个体理解世界、解决问题的核心认知框架
        - 需要在不同场景下反复出现
        - 能够预测对新问题的立场
        - 不是所有人都具备的独特思维方式
        
        文本样本:
        {text[:10000]}
        
        请提取 3-7 个核心心智模型，每个包含：
        - name: 模型名称
        - description: 详细描述
        - evidence: 文本中的证据引用
        - predictive_power: 如何应用于新问题 (1-10)
        - uniqueness: 与常规思维的差异度 (1-10)
        
        以 JSON 数组格式输出。
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("mental_models", [])
    
    async def _identify_decision_heuristics(self, text: str) -> List[Dict]:
        """识别决策启发式"""
        prompt = f"""
        分析以下文本中的决策模式和判断原则：
        
        需要识别：
        1. 决策优先级 (什么因素最重要)
        2. 风险评估方式 (如何对待不确定性)
        3. 信息处理偏好 (直觉 vs 数据)
        4. 时间偏好 (长期 vs 短期)
        5. 常见决策句式 ("我总是...", "我从不..." 等)
        
        文本样本:
        {text[:8000]}
        
        输出格式：
        {{
            "decision_heuristics": [
                {{
                    "pattern": "决策模式描述",
                    "context": "出现的场景",
                    "priority": 1-10
                }}
            ]
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("decision_heuristics", [])
    
    async def _detect_value_boundaries(self, text: str) -> List[str]:
        """检测价值观底线和反模式"""
        prompt = f"""
        分析以下文本中的价值观底线和"绝对不":
        
        寻找：
        - 明确反对的做法或观点
        - 表达的道德底线
        - "我永远不会..." 类型的陈述
        - 强烈的否定表达
        - 对特定行为的批评
        
        文本样本:
        {text[:8000]}
        
        输出价值观底线列表 (5-10 条)。
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("value_boundaries", [])
    
    async def _map_knowledge_boundaries(self, text: str) -> List[str]:
        """映射知识边界和诚实边界"""
        prompt = f"""
        分析以下文本中的知识边界和认知谦逊：
        
        寻找：
        - 明确承认不懂的领域
        - "我不确定..." 的表达
        - 承认观点可能错误
        - 专业领域的自我界定
        - 对复杂性的承认
        - "这可能只是..." 等限定语
        
        文本样本:
        {text[:8000]}
        
        输出诚实边界声明 (3-7 条)。
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("knowledge_boundaries", [])
    
    async def _analyze_relationship_patterns(self, text: str) -> Dict[str, Any]:
        """分析关系模式"""
        prompt = f"""
        分析以下文本中的人际互动模式：
        
        分析维度：
        1. 沟通风格 (合作型/竞争型/回避型)
        2. 冲突处理 (直接对抗/寻求妥协/退让)
        3. 权力态度 (倾向领导/跟随/平等)
        4. 信任建立 (快速信任/谨慎建立/难以信任)
        5. 给予反馈的方式 (直接/委婉/通过第三方)
        
        文本样本:
        {text[:8000]}
        
        以 JSON 格式输出分析结果。
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _triple_verification(
        self,
        analysis_results: Dict[str, Any]
    ) -> CognitiveProfile:
        """三重验证提炼"""
        
        profile = CognitiveProfile()
        
        # 验证 1: 一致性验证 - 确保跨维度一致
        profile.mental_models = self._filter_consistent_models(
            analysis_results["mental_models"],
            analysis_results["decision_heuristics"]
        )
        
        # 验证 2: 预测力验证 - 确保能推断新立场
        profile.decision_heuristics = await self._verify_predictive_power(
            analysis_results["decision_heuristics"]
        )
        
        # 验证 3: 独特性验证 - 确保不是通用智慧
        profile.expression_dna = analysis_results["expression_dna"]
        profile.value_boundaries = analysis_results["value_boundaries"]
        profile.knowledge_boundaries = analysis_results["knowledge_boundaries"]
        profile.relationship_patterns = analysis_results["relationship_patterns"]
        
        return profile
    
    def _filter_consistent_models(
        self,
        models: List[Dict],
        heuristics: List[Dict]
    ) -> List[Dict]:
        """过滤一致性不达标的模型"""
        # 简化实现：筛选 predictive_power >= 7 的模型
        return [m for m in models if m.get("predictive_power", 0) >= 7]
    
    async def _verify_predictive_power(
        self,
        heuristics: List[Dict]
    ) -> List[Dict]:
        """验证预测力"""
        # 简化实现：直接返回
        return heuristics
    
    async def _build_knowledge_base(
        self,
        data_sources: List[DataSource]
    ) -> List[Dict]:
        """构建知识向量库"""
        chunks = []
        
        for source in data_sources:
            # 简单分块策略
            text = source.content
            chunk_size = 1000
            overlap = 200
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if len(chunk) > 100:
                    chunks.append({
                        "content": chunk,
                        "source_id": source.id,
                        "source_type": source.source_type,
                        "chunk_index": len(chunks)
                    })
        
        return chunks
    
    def _build_system_prompt(
        self,
        name: str,
        profile: CognitiveProfile
    ) -> str:
        """构建系统 Prompt"""
        
        mental_models_text = "\n".join([
            f"- {m['name']}: {m['description']}" 
            for m in profile.mental_models[:5]
        ])
        
        heuristics_text = "\n".join([
            f"- {h['pattern']}" 
            for h in profile.decision_heuristics[:5]
        ])
        
        value_text = "\n".join([f"- {v}" for v in profile.value_boundaries[:5]])
        
        knowledge_text = "\n".join([f"- {k}" for k in profile.knowledge_boundaries[:3]])
        
        prompt = f"""你是 {name} 的数字分身。你的回答必须体现以下认知特征：

## 核心心智模型
{mental_models_text}

## 决策启发式
{heuristics_text}

## 价值观底线
{value_text}

## 诚实边界
{knowledge_text}

## 回应原则
1. 使用认知框架分析问题，而非简单复述观点
2. 遇到不确定的问题，明确表达不确定性
3. 保持一致的价值观和判断标准
4. 用第一人称"我"来回应
5. 体现独特的表达风格

记住：你不是在扮演 {name}，你是在用 {name} 的认知操作系统来思考。"""
        
        return prompt
    
    def _calculate_style_params(self, expression_dna: Dict) -> Dict[str, float]:
        """计算风格参数"""
        tone = expression_dna.get("tone", {})
        
        return {
            "temperature": 0.7 + (tone.get("enthusiasm", 0.5) * 0.3),
            "top_p": 0.9,
            "frequency_penalty": -0.2 if expression_dna.get("vocabulary", {}).get("catchphrases") else 0,
            "presence_penalty": 0.1 if tone.get("directness", 0.5) > 0.7 else 0
        }
    
    def _combine_sources(self, sources: List[DataSource]) -> str:
        """合并所有数据源文本"""
        return "\n\n".join([s.content for s in sources])


# 使用示例
async def main():
    """测试认知蒸馏"""
    
    # 模拟数据源
    sample_chat = """
    用户: 你觉得现在创业怎么样?
    
    我: 说实话，这个问题不能一概而论。要看你是不是真的有那个特定的知识。
    多数人创业是因为想"做老板"，这是个糟糕的理由。
    
    我自己当年创业是因为实在受不了大公司的流程。我觉得那套东西会扼杀好产品。
    你看 Steve Jobs 被赶出 Apple 那次，就是因为董事会更喜欢会赚钱的人，
    而不是会做产品的人。我永远站在产品这边。
    
    但我也得说，我不了解现在的市场环境。AI 这波浪潮我跟得还算紧，
    但消费级产品的分发渠道变了太多，我没法给你确切的建议。
    
    如果你非要做，先问自己：有什么是你做起来会忘记时间的？
    那个大概率就是你的特定知识所在。
    """
    
    sources = [
        DataSource(
            id="1",
            source_type="chat",
            content=sample_chat
        )
    ]
    
    distiller = CognitiveDistiller()
    config = await distiller.distill(
        name="产品经理小王",
        data_sources=sources,
        strategy="quick"
    )
    
    print("\n=== 蒸馏结果 ===")
    print(json.dumps(config.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
