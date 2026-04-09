"""
对话生成服务
支持多 LLM 提供商
"""
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.avatar import Avatar
from app.models.conversation import Conversation, Message
from app.services.llm import llm_manager, LLMProvider


async def generate_avatar_response(
    avatar: Avatar,
    conversation: Conversation,
    user_message: str,
    db: AsyncSession,
    provider: Optional[str] = None
) -> Tuple[str, Optional[Dict[str, float]]]:
    """
    生成数字分身的回复
    
    Args:
        avatar: 数字分身
        conversation: 对话
        user_message: 用户消息
        db: 数据库会话
        provider: 可选，指定 LLM 提供商
    
    Returns:
        (回复内容, 情绪状态)
    """
    # 构建系统提示
    system_prompt = avatar.system_prompt or f"你是 {avatar.name} 的数字分身。请用你独特的认知风格回应。"
    
    # 获取风格参数
    style_config = avatar.style_config or {}
    temperature = style_config.get("temperature", 0.7)
    max_tokens = style_config.get("max_tokens", 500)
    
    # 获取历史消息（最近的 10 条）
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history = result.scalars().all()
    
    # 构建消息历史
    messages = [{"role": "system", "content": system_prompt}]
    
    # 添加历史消息（倒序转为正序）
    for msg in reversed(history):
        role = "assistant" if (msg.message_metadata or {}).get("is_ai", False) else "user"
        messages.append({"role": role, "content": msg.content})
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": user_message})
    
    try:
        # 确定使用哪个 LLM 提供商
        llm_provider = None
        if provider:
            llm_provider = LLMProvider(provider.lower())
        
        # 获取客户端并生成回复
        client = llm_manager.get_client(llm_provider)
        
        print(f"[Chat] Generating response using {client.provider.value} for avatar {avatar.name}")
        
        response = await client.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 分析情绪（简化版本）
        emotion = await analyze_emotion(response)
        
        return response, emotion
    
    except Exception as e:
        print(f"[Chat] Error generating response: {e}")
        # API 失败时返回模拟回复
        mock_responses = [
            f"你好！我是 {avatar.name}。很高兴和你对话。",
            f"这是一个很有趣的话题。作为 {avatar.name}，我认为...",
            "我理解你的想法。从我的角度来看...",
            "确实如此。这让我想到...",
            "有意思的观点。让我思考一下...",
        ]
        import random
        response = random.choice(mock_responses)
        return response, {"pleasure": 0.2, "arousal": 0.3, "dominance": 0.1}


async def analyze_emotion(text: str) -> Dict[str, float]:
    """
    分析文本的情绪状态（PAD 模型）
    
    Returns:
        {"pleasure": float, "arousal": float, "dominance": float}
    """
    # 简化版本：使用简单的关键词匹配
    # 实际生产环境应该使用 emotion detection 模型
    
    positive_words = ["好", "棒", "优秀", "喜欢", "开心", "兴奋", "赞同", "支持", "确实", "有道理"]
    negative_words = ["差", "糟", "讨厌", "难过", "愤怒", "反对", "拒绝", "不行", "不对", "错误"]
    excited_words = ["非常", "极其", "绝对", "必须", "一定", "太", "真的"]
    dominant_words = ["应该", "需要", "必须", "我认为", "我坚信"]
    
    pleasure = 0.0
    arousal = 0.0
    dominance = 0.0
    
    for word in positive_words:
        if word in text:
            pleasure += 0.15
    
    for word in negative_words:
        if word in text:
            pleasure -= 0.15
    
    for word in excited_words:
        if word in text:
            arousal += 0.2
    
    for word in dominant_words:
        if word in text:
            dominance += 0.15
    
    # 标点符号分析
    if "!" in text or "！" in text:
        arousal += 0.2
    
    if "?" in text or "？" in text:
        arousal += 0.1
        dominance -= 0.1
    
    # 限制范围
    pleasure = max(-1, min(1, pleasure))
    arousal = max(-1, min(1, arousal))
    dominance = max(-1, min(1, dominance))
    
    return {
        "pleasure": round(pleasure, 2),
        "arousal": round(arousal, 2),
        "dominance": round(dominance, 2)
    }


async def generate_streaming_response(
    avatar: Avatar,
    messages: list,
    provider: Optional[str] = None
) -> str:
    """生成流式响应（用于 WebSocket）"""
    system_prompt = avatar.system_prompt or f"你是 {avatar.name} 的数字分身。"
    
    all_messages = [{"role": "system", "content": system_prompt}]
    all_messages.extend(messages)
    
    style_config = avatar.style_config or {}
    temperature = style_config.get("temperature", 0.7)
    max_tokens = style_config.get("max_tokens", 500)
    
    try:
        # 确定使用哪个 LLM 提供商
        llm_provider = None
        if provider:
            llm_provider = LLMProvider(provider.lower())
        
        client = llm_manager.get_client(llm_provider)
        
        full_response = ""
        
        async for chunk in client.chat_completion_stream(
            messages=all_messages,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            full_response += chunk
            yield chunk
    
    except Exception as e:
        print(f"[Chat] Error in streaming response: {e}")
        error_msg = f"[错误: {str(e)[:50]}]"
        yield error_msg
