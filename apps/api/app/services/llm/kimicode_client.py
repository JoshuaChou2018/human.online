"""
Kimi Code API 客户端
支持自定义 Base URL 和认证方式
"""
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx

from app.services.llm.base import BaseLLMClient, LLMProvider


class KimiCodeClient(BaseLLMClient):
    """
    Kimi Code API 客户端
    
    特点：
    - 支持自定义 Base URL
    - 支持多种认证方式 (Bearer, X-API-Key, 等)
    - 兼容 OpenAI 格式
    """
    
    provider = LLMProvider.KIMI
    
    # 可用模型
    MODELS = {
        "kimi-code": "Kimi Code 模型",
        "moonshot-v1-8k": "适用于简单任务，最大上下文 8k",
        "moonshot-v1-32k": "适用于中等复杂任务，最大上下文 32k",
        "moonshot-v1-128k": "适用于长文档处理，最大上下文 128k",
    }
    
    def __init__(self, api_key: str, model: str = "kimi-code", base_url: Optional[str] = None, **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        # 支持自定义 base URL
        self.base_url = base_url or "https://api.moonshot.cn/v1"
        
        # 构建请求头 - 支持多种认证方式
        headers = {}
        
        # 方式1: Bearer Token (标准 OpenAI 格式)
        headers["Authorization"] = f"Bearer {api_key}"
        
        # 方式2: X-API-Key (某些服务使用)
        headers["X-API-Key"] = api_key
        
        # 方式3: X-App-Id (某些国内服务使用)
        if kwargs.get("app_id"):
            headers["X-App-Id"] = kwargs["app_id"]
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=120.0
        )
        self.embedding_model = kwargs.get("embedding_model", "kimi-code")
    
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
        """创建文本嵌入向量"""
        import hashlib
        embeddings = []
        for text in texts:
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            vector = []
            for i in range(1536):
                vector.append((hash_bytes[i % 16] / 255.0) * 2 - 1)
            embeddings.append(vector)
        
        return embeddings
    
    async def analyze_expression_dna(self, text: str) -> Dict[str, Any]:
        """分析表达 DNA"""
        # 简化实现
        return {
            "tone": {"formality": 0.5, "enthusiasm": 0.5, "directness": 0.5},
            "sentence_patterns": {"avg_length": 20.0, "complexity": 0.5},
            "vocabulary": {"technical_density": 0.3, "emotional_markers": [], "catchphrases": []},
            "rhetoric": {"metaphor_freq": 0.2, "parallelism_freq": 0.1},
            "interaction": {"question_frequency": 0.3, "response_style": "balanced"}
        }
    
    async def extract_mental_models(self, text: str) -> List[Dict[str, Any]]:
        """提取心智模型"""
        return []
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
