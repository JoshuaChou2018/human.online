"""
LLM 客户端基类 - 统一接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """支持的 LLM 提供商"""
    OPENAI = "openai"
    KIMI = "kimi"  # Moonshot
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"
    DEEPSEEK = "deepseek"


@dataclass
class LLMMessage:
    """统一的消息格式"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None  # 用于区分不同分身


@dataclass
class LLMResponse:
    """统一的响应格式"""
    content: str
    model: str
    provider: LLMProvider
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


@dataclass
class EmbeddingResponse:
    """统一的 Embedding 响应格式"""
    embeddings: List[List[float]]
    model: str
    usage: Optional[Dict[str, int]] = None


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""
    
    provider: LLMProvider
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """非流式聊天完成"""
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        pass
    
    @abstractmethod
    async def create_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """创建文本嵌入向量"""
        pass
    
    @abstractmethod
    async def analyze_expression_dna(self, text: str) -> Dict[str, Any]:
        """分析表达 DNA"""
        pass
    
    @abstractmethod
    async def extract_mental_models(self, text: str) -> List[Dict[str, Any]]:
        """提取心智模型"""
        pass
    
    def _build_system_prompt_for_analysis(self) -> str:
        """构建用于认知分析的系统提示"""
        return """你是一个专业的认知科学和语言分析专家。你的任务是分析文本中的认知特征和思维模式。

你需要以 JSON 格式返回分析结果，确保：
1. 分析基于文本中的实际证据
2. 提取的特征具有独特性和一致性
3. 格式严格遵循要求
"""


class LLMManager:
    """LLM 管理器 - 管理多个 LLM 客户端"""
    
    def __init__(self):
        self._clients: Dict[LLMProvider, BaseLLMClient] = {}
        self._default_provider: Optional[LLMProvider] = None
    
    def register_client(self, provider: LLMProvider, client: BaseLLMClient, is_default: bool = False):
        """注册 LLM 客户端"""
        self._clients[provider] = client
        if is_default or self._default_provider is None:
            self._default_provider = provider
    
    def get_client(self, provider: Optional[LLMProvider] = None) -> BaseLLMClient:
        """获取指定或默认的 LLM 客户端"""
        if provider is None:
            provider = self._default_provider
        
        if provider not in self._clients:
            raise ValueError(f"LLM provider {provider} not registered")
        
        return self._clients[provider]
    
    def get_available_providers(self) -> List[LLMProvider]:
        """获取所有可用的提供商"""
        return list(self._clients.keys())
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """使用指定或默认客户端进行聊天"""
        client = self.get_client(provider)
        return await client.chat_completion(messages, **kwargs)
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """使用指定或默认客户端进行流式聊天"""
        client = self.get_client(provider)
        async for chunk in client.chat_completion_stream(messages, **kwargs):
            yield chunk


# 全局 LLM 管理器实例
llm_manager = LLMManager()
