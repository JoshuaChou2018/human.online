"""
OpenAI API 客户端 - 实现基类接口
"""
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI

from app.services.llm.base import BaseLLMClient, LLMProvider


class OpenAIClient(BaseLLMClient):
    """OpenAI API 客户端"""
    
    provider = LLMProvider.OPENAI
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """非流式聊天完成"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def create_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """创建文本嵌入向量"""
        response = await self.client.embeddings.create(
            model=model or self.embedding_model,
            input=texts
        )
        
        return [item.embedding for item in response.data]
    
    async def analyze_expression_dna(self, text: str) -> Dict[str, Any]:
        """分析表达 DNA"""
        prompt = f"""
分析以下文本的表达风格特征，提取"表达 DNA"。

需要分析的维度：
1. 语气特征 (formality, enthusiasm, directness) - 0-1 之间的值
2. 句式偏好 (avg_length, complexity)
3. 词汇特点 (technical_density, emotional_markers, catchphrases)
4. 修辞习惯 (metaphor_freq, parallelism_freq)
5. 互动模式 (question_frequency, response_style)

文本样本:
{text[:3000]}

请以 JSON 格式输出分析结果：
{{
    "tone": {{"formality": float, "enthusiasm": float, "directness": float}},
    "sentence_patterns": {{"avg_length": float, "complexity": float}},
    "vocabulary": {{"technical_density": float, "emotional_markers": [str], "catchphrases": [str]}},
    "rhetoric": {{"metaphor_freq": float, "parallelism_freq": float}},
    "interaction": {{"question_frequency": float, "response_style": str}}
}}
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt_for_analysis()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def extract_mental_models(self, text: str) -> List[Dict[str, Any]]:
        """提取心智模型"""
        prompt = f"""
分析以下文本中体现的认知框架和心智模型。

心智模型定义：
- 是个体理解世界、解决问题的核心认知框架
- 需要在不同场景下反复出现
- 能够预测对新问题的立场
- 不是所有人都具备的独特思维方式

请提取 3-7 个核心心智模型，每个包含：
- name: 模型名称
- description: 详细描述
- evidence: 文本中的证据引用

文本样本:
{text[:5000]}

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
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt_for_analysis()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("mental_models", [])
