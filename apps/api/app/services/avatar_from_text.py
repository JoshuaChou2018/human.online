"""
基于文本描述创建数字分身

当用户不想上传数据时，只需要提供一段文本描述，
后端使用 LLM 自动生成完整的分身配置。
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.models.avatar import Avatar, AvatarType, AvatarStatus
from app.models.simulation import SandboxMember
from app.models.weaving_progress import WeavingProgress, WeavingStage
from app.services.llm import llm_manager


AVATAR_GENERATION_PROMPT = """你是一位专业的数字分身设计师。请根据用户提供的描述，生成一个完整的数字分身配置。

用户描述：
{name}
{description}

请生成以下 JSON 格式的配置：

```json
{{
  "system_prompt": "详细的系统提示词，定义这个分身的身份、性格、说话风格、价值观等。应该让 LLM 能够扮演这个角色。",
  "mind_weave_profile": {{
    "mindThreads": {{
      "rationality": 0.0-1.0,
      "emotionality": 0.0-1.0,
      "confidence": 0.0-1.0,
      "openness": 0.0-1.0,
      "analytical": 0.0-1.0,
      "synthesis": 0.0-1.0
    }},
    "identityCard": {{
      "archetype": "原型标签（如：智者、艺术家、领导者等）",
      "thinkingStyle": "思维方式描述",
      "speechPattern": "说话风格特点",
      "decisionTendency": "决策倾向",
      "cognitiveBiases": "认知特点或偏见",
      "knowledgeDomains": ["知识领域1", "知识领域2"]
    }}
  }},
  "cognitive_config": {{
    "mind_model": "心智模型描述",
    "decision_heuristics": ["启发式1", "启发式2"],
    "reasoning_style": "推理风格",
    "knowledge_scope": ["知识范围1", "知识范围2"]
  }},
  "expression_dna": {{
    "tone": "语气特点",
    "vocabulary": ["高频词汇1", "高频词汇2"],
    "sentence_structure": "句式特点",
    "rhetorical_devices": ["修辞手法1", "修辞手法2"]
  }},
  "style_config": {{
    "temperature": 0.0-1.0,
    "top_p": 0.0-1.0,
    "presence_penalty": -2.0 to 2.0,
    "frequency_penalty": -2.0 to 2.0
  }},
  "short_description": "一句话描述这个分身"
}}
```

要求：
1. 基于描述中的信息，合理推断分身的特征
2. system_prompt 必须详细且具体，能让 LLM 准确扮演这个角色
3. 数值类参数根据描述中的性格特点合理设定
4. 返回必须是合法的 JSON 格式
"""


async def generate_avatar_config_from_text(name: str, description: str) -> Dict[str, Any]:
    """
    使用 LLM 根据文本描述生成分身配置
    """
    # 构建提示词
    prompt = AVATAR_GENERATION_PROMPT.format(
        name=name,
        description=description or "（无详细描述）"
    )
    
    messages = [
        {"role": "system", "content": "You are a professional avatar designer. Generate valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        # 调用 LLM
        response = await llm_manager.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=3000
        )
        
        # 提取 JSON
        content = response.strip()
        
        # 处理可能的 markdown 代码块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        config = json.loads(content)
        
        # 验证必要字段
        required_fields = ["system_prompt", "mind_weave_profile", "cognitive_config", 
                          "expression_dna", "style_config"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        return config
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse avatar config: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate avatar config: {str(e)}"
        )


async def create_avatar_from_text_description(
    user: User,
    name: str,
    description: str,
    is_public: bool,
    db: AsyncSession
) -> Avatar:
    """
    基于文本描述创建数字分身
    
    流程：
    1. 检查用户免费额度
    2. 使用 LLM 根据描述生成分身配置
    3. 创建 avatar 记录
    4. 加入沙盒（如果是公开的）
    5. 启动编织任务
    """
    # 检查免费额度
    if not user.can_create_free_avatar:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free avatar quota exceeded. Please upgrade your plan."
        )
    
    # 使用 LLM 生成配置
    config = await generate_avatar_config_from_text(name, description)
    
    # 创建 avatar
    now = datetime.utcnow()
    avatar = Avatar(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name,
        description=config.get("short_description") or description,
        avatar_type=AvatarType.PERSONAL,
        status=AvatarStatus.WEAVING,
        is_public=is_public,
        auto_join_sandbox=is_public,
        sandbox_status="inactive" if not is_public else "active",
        system_prompt=config["system_prompt"],
        mind_weave_profile=config["mind_weave_profile"],
        cognitive_config=config["cognitive_config"],
        expression_dna=config["expression_dna"],
        style_config=config["style_config"],
        created_at=now,
        updated_at=now
    )
    
    db.add(avatar)
    
    # 更新用户已创建数量
    user.avatars_created += 1
    
    # 如果是公开的，加入沙盒
    if is_public:
        member = SandboxMember(
            id=uuid.uuid4(),
            avatar_id=avatar.id,
            user_id=user.id,
            status="active",
            total_messages=0,
            total_interactions=0,
            last_activity_at=now,
            joined_at=now
        )
        db.add(member)
    
    await db.flush()
    await db.commit()
    await db.refresh(avatar)
    
    # 启动编织任务（模拟编织过程）
    # 由于是基于文本描述，编织过程实际上是验证和完善配置
    import asyncio
    from app.services.mindweave.weaving import start_weaving_task
    
    # 启动异步任务来更新编织进度
    asyncio.create_task(_simulate_weaving_for_text_avatar(str(avatar.id)))
    
    return avatar


async def _simulate_weaving_for_text_avatar(avatar_id: str):
    """
    模拟基于文本创建的分身的编织过程
    
    由于配置已经由 LLM 生成，编织过程主要是：
    1. 记录编织进度
    2. 验证配置完整性
    3. 更新状态为 READY
    """
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.services.weaving_tracker import get_weaving_tracker
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取 avatar
            result = await db.execute(
                select(Avatar).where(Avatar.id == uuid.UUID(avatar_id))
            )
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                print(f"Avatar {avatar_id} not found")
                return
            
            # 使用 WeavingTracker 来追踪进度
            tracker = get_weaving_tracker(avatar_id, db)
            await tracker.initialize()
            
            # 添加初始日志
            await tracker.add_log(WeavingStage.PREPARING, "📝 开始基于文本描述创建数字分身", "info")
            await tracker.add_log(WeavingStage.PREPARING, "✨ LLM 已生成初始配置", "success")
            await asyncio.sleep(0.5)
            
            # 模拟各阶段进度（文本描述创建的分身）
            stages = [
                (WeavingStage.ANALYZING_MIND_CORE, "🧠 分析思维内核特征..."),
                (WeavingStage.ANALYZING_EXPRESSION, "💬 提取表达风格模式..."),
                (WeavingStage.ANALYZING_VALUES, "⚖️ 识别价值体系..."),
                (WeavingStage.WEAVING_MIND, "🧵 编织思维内核..."),
                (WeavingStage.GENERATING_IDENTITY, "🖼️ 生成身份认证卡..."),
            ]
            
            for stage, message in stages:
                await tracker.set_stage(stage, message)
                await tracker.update_progress(stage, 50, f"正在{message[2:]}")
                await asyncio.sleep(0.8)
                await tracker.complete_stage(stage, message=f"{message[2:]}完成")
            
            # 完成编织
            await tracker.complete()
            
            # 更新 avatar 状态
            avatar.status = AvatarStatus.READY
            await db.commit()
            
            print(f"Avatar {avatar_id} text-based weaving completed")
            
        except Exception as e:
            print(f"Text avatar weaving failed for {avatar_id}: {e}")
            import traceback
            traceback.print_exc()
            # 尝试标记为失败
            try:
                tracker = get_weaving_tracker(avatar_id, db)
                await tracker.fail(str(e))
            except:
                pass
