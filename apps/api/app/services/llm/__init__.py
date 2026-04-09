"""
LLM 服务模块

支持多个 LLM 提供商：
- OpenAI (GPT-4, GPT-3.5)
- Kimi/Moonshot (月之暗面)
- Kimi Code (Kimi 代码版)
- DeepSeek
- Anthropic (Claude)
- 更多即将支持...
"""
from app.core.config import settings
from app.services.llm.base import llm_manager, LLMProvider, BaseLLMClient
from app.services.llm.openai_client import OpenAIClient
from app.services.llm.kimi_client import KimiClient
from app.services.llm.kimicode_client import KimiCodeClient
from app.services.llm.deepseek_client import DeepSeekClient


def init_llm_clients():
    """初始化所有配置的 LLM 客户端"""
    
    # 注册 OpenAI 客户端
    if settings.OPENAI_API_KEY:
        openai_client = OpenAIClient(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            embedding_model=settings.OPENAI_EMBEDDING_MODEL
        )
        llm_manager.register_client(
            LLMProvider.OPENAI,
            openai_client,
            is_default=(settings.DEFAULT_LLM_PROVIDER == "openai")
        )
        print(f"✅ Registered OpenAI client with model: {settings.OPENAI_MODEL}")
    
    # 注册 Kimi 客户端
    if settings.KIMI_API_KEY:
        kimi_client = KimiClient(
            api_key=settings.KIMI_API_KEY,
            model=settings.KIMI_MODEL,
            api_id=settings.KIMI_API_ID
        )
        llm_manager.register_client(
            LLMProvider.KIMI,
            kimi_client,
            is_default=(settings.DEFAULT_LLM_PROVIDER == "kimi")
        )
        api_id_info = f" (with API ID: {settings.KIMI_API_ID})" if settings.KIMI_API_ID else ""
        print(f"✅ Registered Kimi client with model: {settings.KIMI_MODEL}{api_id_info}")
    
    # 注册 Kimi Code 客户端
    if settings.KIMICODE_API_KEY:
        kimicode_client = KimiCodeClient(
            api_key=settings.KIMICODE_API_KEY,
            model=settings.KIMICODE_MODEL,
            base_url=settings.KIMICODE_BASE_URL
        )
        llm_manager.register_client(
            LLMProvider.KIMI,
            kimicode_client,
            is_default=(settings.DEFAULT_LLM_PROVIDER == "kimicode")
        )
        base_url_info = f" (base_url: {settings.KIMICODE_BASE_URL})" if settings.KIMICODE_BASE_URL else ""
        print(f"✅ Registered Kimi Code client with model: {settings.KIMICODE_MODEL}{base_url_info}")
    
    # 注册 DeepSeek 客户端 (优先级最高)
    if settings.DEEPSEEK_API_KEY:
        deepseek_client = DeepSeekClient(
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.DEEPSEEK_MODEL
        )
        llm_manager.register_client(
            LLMProvider.OPENAI,  # 使用 OPENAI provider 类型
            deepseek_client,
            is_default=(settings.DEFAULT_LLM_PROVIDER == "deepseek")
        )
        print(f"✅ Registered DeepSeek client with model: {settings.DEEPSEEK_MODEL}")
    
    # 检查是否至少注册了一个客户端
    if not llm_manager.get_available_providers():
        raise RuntimeError(
            "No LLM clients registered. Please configure at least one API key "
            "(OPENAI_API_KEY, KIMI_API_KEY, KIMICODE_API_KEY, or DEEPSEEK_API_KEY)"
        )
    
    print(f"🤖 Default LLM provider: {llm_manager._default_provider.value}")


# 导出
__all__ = [
    "llm_manager",
    "LLMProvider",
    "BaseLLMClient",
    "OpenAIClient",
    "KimiClient",
    "KimiCodeClient",
    "DeepSeekClient",
    "init_llm_clients",
]
