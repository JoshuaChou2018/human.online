"""
Kimi (Moonshot) API 客户端 - 月之暗面
API 文档: https://platform.moonshot.cn/docs

Kimi API 兼容 OpenAI 格式，可以复用大部分代码
"""
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx

from app.services.llm.base import BaseLLMClient, LLMProvider


class KimiClient(BaseLLMClient):
    """
    Kimi (Moonshot) API 客户端
    
    特点：
    - 支持超长上下文（200k tokens）
    - 对中文支持更好
    - API 兼容 OpenAI 格式
    """
    
    provider = LLMProvider.KIMI
    BASE_URL = "https://api.moonshot.cn/v1"
    
    # 可用模型
    MODELS = {
        "moonshot-v1-8k": "适用于简单任务，最大上下文 8k",
        "moonshot-v1-32k": "适用于中等复杂任务，最大上下文 32k",
        "moonshot-v1-128k": "适用于长文档处理，最大上下文 128k",
    }
    
    def __init__(self, api_key: str, model: str = "moonshot-v1-32k", **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        # 构建请求头
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # 中国特别版可能需要 API ID
        api_id = kwargs.get("api_id")
        if api_id:
            headers["X-Api-Id"] = api_id
        
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=120.0
        )
        # Kimi 没有专门的 embedding API，使用 text-embedding 替代
        self.embedding_model = kwargs.get("embedding_model", "moonshot-v1-8k")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """非流式聊天完成"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        response = await self.client.post(
            "/chat/completions",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return data["choices"][0]["message"]["content"]
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        async with self.client.stream(
            "POST",
            "/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or line == "data: [DONE]":
                    continue
                
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def create_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        创建文本嵌入向量
        
        Kimi 没有专门的 embedding API，这里使用一种变通方案：
        使用模型生成向量表示（简化版本）
        """
        # 注意：Kimi 目前没有官方的 Embedding API
        # 这里返回一个模拟的嵌入向量，实际生产环境应该：
        # 1. 使用 OpenAI 的 Embedding API
        # 2. 使用本地的 Embedding 模型（如 BGE-M3）
        # 3. 等待 Kimi 官方发布 Embedding API
        
        # 临时方案：使用简单的哈希模拟（仅用于演示）
        import hashlib
        embeddings = []
        for text in texts:
            # 使用哈希生成伪向量（实际项目中请替换为真实 Embedding）
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # 转换为 1536 维向量（与 OpenAI 兼容）
            vector = []
            for i in range(1536):
                vector.append((hash_bytes[i % 16] / 255.0) * 2 - 1)
            embeddings.append(vector)
        
        return embeddings
    
    async def analyze_expression_dna(self, text: str) -> Dict[str, Any]:
        """分析表达 DNA - 针对中文优化"""
        prompt = f"""
作为专业的语言风格分析师，请分析以下文本的表达风格特征，提取"表达 DNA"。

需要分析的维度：
1. 语气特征 (formality, enthusiasm, directness) - 0-1 之间的值
   - formality: 正式程度（使用书面语、敬语的频率）
   - enthusiasm: 热情程度（情感表达强度）
   - directness: 直接程度（表达是否直截了当）

2. 句式偏好 (avg_length, complexity)
   - avg_length: 平均句长（字数）
   - complexity: 句式复杂度（从句、修饰语的使用）

3. 词汇特点 (technical_density, emotional_markers, catchphrases)
   - technical_density: 专业术语密度
   - emotional_markers: 情感标记词（如：啊、呢、吧、嘛）
   - catchphrases: 口头禅或高频用语

4. 修辞习惯 (metaphor_freq, parallelism_freq)
   - metaphor_freq: 比喻使用频率
   - parallelism_freq: 排比/对偶使用频率

5. 互动模式 (question_frequency, response_style)
   - question_frequency: 提问频率
   - response_style: 回应风格描述

文本样本:
{text[:8000]}

请以 JSON 格式输出分析结果，确保数值在 0-1 之间：
{{
    "tone": {{"formality": float, "enthusiasm": float, "directness": float}},
    "sentence_patterns": {{"avg_length": float, "complexity": float}},
    "vocabulary": {{"technical_density": float, "emotional_markers": [str], "catchphrases": [str]}},
    "rhetoric": {{"metaphor_freq": float, "parallelism_freq": float}},
    "interaction": {{"question_frequency": float, "response_style": str}}
}}
"""
        
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self._build_system_prompt_for_analysis()},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        data = response.json()
        
        return json.loads(data["choices"][0]["message"]["content"])
    
    async def extract_mental_models(self, text: str) -> List[Dict[str, Any]]:
        """提取心智模型 - 针对中文优化"""
        prompt = f"""
作为认知科学专家，请分析以下文本中体现的认知框架和心智模型。

心智模型定义：
- 是个体理解世界、解决问题的核心认知框架
- 需要在不同场景下反复出现
- 能够预测对新问题的立场
- 不是所有人都具备的独特思维方式

请提取 3-7 个核心心智模型，每个包含：
- name: 模型名称（简洁的中文名称）
- description: 详细描述（解释这个模型的核心逻辑）
- evidence: 文本中的证据引用（原文片段）

文本样本:
{text[:12000]}

以 JSON 格式输出：
{{
    "mental_models": [
        {{
            "name": str,
            "description": str,
            "evidence": [str]
        }}
    ]
}}
"""
        
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self._build_system_prompt_for_analysis()},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        data = response.json()
        
        result = json.loads(data["choices"][0]["message"]["content"])
        return result.get("mental_models", [])
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
    
    def _build_system_prompt_for_analysis(self) -> str:
        """构建用于认知分析的系统提示 - 中文优化版"""
        return """你是专业的认知科学和语言分析专家，擅长分析中文文本的认知特征。

你的分析原则：
1. 基于文本中的实际证据，不凭空臆断
2. 关注中文特有的表达习惯（如成语、俗语、语气词）
3. 识别深层的思维模式，而非表面的观点
4. 输出严格的 JSON 格式

分析时特别注意：
- 中文的含蓄表达方式
- 上下文依赖的语义
- 文化特定的思维模式"""
