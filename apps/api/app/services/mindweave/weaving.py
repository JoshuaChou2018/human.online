"""
思维编织服务 (Mind Weaving Service)

基于 MindWeave 理论，从个人数据中提取六维思维线索，
编织成完整的数字 psyche。
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.avatar import Avatar, DataSource, AvatarStatus
from app.models.weaving_progress import WeavingStage
from app.services.llm import llm_manager, LLMProvider
from app.services.weaving_tracker import get_weaving_tracker


async def start_weaving_task(
    avatar_id: str, 
    data_source_ids: List[str], 
    provider: Optional[str] = None
) -> str:
    """
    启动思维编织任务
    
    Args:
        avatar_id: psyche ID
        data_source_ids: 数据源 ID 列表
        provider: 可选，指定 LLM 提供商
    
    Returns:
        task_id
    """
    task_id = f"weave_{avatar_id}"
    print(f"[MindWeave] 启动编织任务: {task_id}, 数据源: {len(data_source_ids)} 个")
    
    from app.core.database import AsyncSessionLocal
    
    async def run_weaving():
        print(f"[MindWeave] 开始执行编织: {task_id}")
        async with AsyncSessionLocal() as db:
            try:
                await process_weaving(avatar_id, data_source_ids, db, provider)
                print(f"[MindWeave] 编织任务完成: {task_id}")
            except Exception as e:
                print(f"[MindWeave] 编织任务异常: {task_id} - {e}")
                import traceback
                traceback.print_exc()
    
    asyncio.create_task(run_weaving())
    
    return task_id


async def process_weaving(
    avatar_id: str,
    data_source_ids: List[str],
    db: AsyncSession,
    provider: Optional[str] = None
):
    """处理思维编织（带进度追踪）"""
    import uuid
    
    tracker = get_weaving_tracker(avatar_id, db)
    
    try:
        # 初始化进度追踪
        await tracker.initialize()
        
        # 设置 Avatar 状态为编织中
        avatar_uuid = uuid.UUID(avatar_id) if isinstance(avatar_id, str) else avatar_id
        result = await db.execute(
            select(Avatar).where(Avatar.id == avatar_uuid)
        )
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            await tracker.fail(f"Avatar {avatar_id} not found")
            return
        
        avatar.status = AvatarStatus.WEAVING
        await db.commit()
        
        # === 准备阶段 ===
        await tracker.set_stage(WeavingStage.PREPARING, "📤 开始编织过程，读取用户数据源...")
        await tracker.update_progress(WeavingStage.PREPARING, 30, "正在获取数据源列表...")
        
        # 获取数据源（将字符串 ID 转换为 UUID）
        data_source_uuids = [uuid.UUID(ds_id) if isinstance(ds_id, str) else ds_id for ds_id in data_source_ids]
        await tracker.add_log(WeavingStage.PREPARING, f"查询数据源 IDs: {data_source_ids}", "info")
        
        result = await db.execute(
            select(DataSource).where(DataSource.id.in_(data_source_uuids))
        )
        data_sources = result.scalars().all()
        
        await tracker.add_log(
            WeavingStage.PREPARING, 
            f"找到 {len(data_sources)} 个数据源",
            "info",
            {"data_source_count": len(data_sources)}
        )
        
        await tracker.update_progress(WeavingStage.PREPARING, 60, "正在提取文本内容...")
        
        # === 文本提取阶段 ===
        await tracker.set_stage(WeavingStage.EXTRACTING_TEXT, "📝 正在从上传文件中提取可分析的文本内容...")
        
        # 合并所有内容
        combined_text = ""
        extracted_sources = []
        
        for i, ds in enumerate(data_sources):
            progress = int((i / len(data_sources)) * 100)
            await tracker.update_progress(
                WeavingStage.EXTRACTING_TEXT, 
                progress,
                f"正在处理: {ds.file_name}"
            )
            
            content = ""
            if ds.extracted_insights:
                insight_content = ds.extracted_insights.get("content_preview", "")
                if isinstance(insight_content, dict):
                    content = insight_content.get("content", "")
                else:
                    content = str(insight_content)
            
            if not content and ds.file_path:
                try:
                    from app.services.storage import read_file_content
                    file_result = await read_file_content(ds.file_path)
                    # 处理可能返回的字典格式（如 PDF/Word 解析结果）
                    if isinstance(file_result, dict):
                        content = file_result.get("content", "")
                    else:
                        content = str(file_result)
                except Exception as e:
                    await tracker.add_log(
                        WeavingStage.EXTRACTING_TEXT,
                        f"读取文件失败: {ds.file_name} - {str(e)}",
                        "warning"
                    )
            
            if content and isinstance(content, str):
                combined_text += content + "\n\n"
                extracted_sources.append({
                    "file_name": ds.file_name,
                    "content_length": len(content)
                })
                await tracker.add_log(
                    WeavingStage.EXTRACTING_TEXT,
                    f"成功提取: {ds.file_name} ({len(content)} 字符)",
                    "success"
                )
        
        if not combined_text:
            await tracker.fail("未能从数据源中提取到有效内容")
            avatar.status = AvatarStatus.DRAFT
            await db.commit()
            return
        
        await tracker.complete_stage(
            WeavingStage.EXTRACTING_TEXT,
            {"extracted_sources": extracted_sources, "total_length": len(combined_text)},
            f"✅ 成功提取 {len(extracted_sources)} 个数据源，共 {len(combined_text)} 字符"
        )
        
        # 设置文本预览
        await tracker.set_text_preview(combined_text[:1000])
        
        # 确定使用哪个 LLM 提供商
        llm_provider = None
        if provider:
            llm_provider = LLMProvider(provider.lower())
        
        client = llm_manager.get_client(llm_provider)
        await tracker.update_llm_stats(
            provider=client.provider.value,
            model=client.model
        )
        
        await tracker.add_log(
            WeavingStage.PREPARING,
            f"🤖 使用 LLM: {client.provider.value} / {client.model}",
            "info"
        )
        
        # 限制文本长度
        analysis_text = combined_text[:8000]
        
        # === 六维线索提取 ===
        
        # 1. 思维内核分析
        await tracker.set_stage(WeavingStage.ANALYZING_MIND_CORE, "🧠 正在分析思维内核（Mind Core）...")
        await tracker.add_log(
            WeavingStage.ANALYZING_MIND_CORE,
            "🔍 识别核心思维框架和认知偏好...",
            "info"
        )
        
        try:
            mind_core = await extract_mind_core(client, analysis_text, tracker)
            await tracker.complete_stage(
                WeavingStage.ANALYZING_MIND_CORE,
                mind_core,
                f"✅ 思维内核分析完成：识别到 {len(mind_core.get('thinking_frameworks', []))} 个思维框架"
            )
        except Exception as e:
            await tracker.add_log(
                WeavingStage.ANALYZING_MIND_CORE,
                f"思维内核分析出错: {str(e)}",
                "warning"
            )
            mind_core = {}
        
        # 2. 表达风格分析
        await tracker.set_stage(WeavingStage.ANALYZING_EXPRESSION, "💬 正在分析表达风格（Expression Style）...")
        await tracker.add_log(
            WeavingStage.ANALYZING_EXPRESSION,
            "🔍 提取语言习惯和表达特征...",
            "info"
        )
        
        try:
            expression_style = await extract_expression_style(client, analysis_text, tracker)
            tone = expression_style.get('tone', {})
            await tracker.complete_stage(
                WeavingStage.ANALYZING_EXPRESSION,
                expression_style,
                f"✅ 表达风格分析完成：正式度 {tone.get('formality', 0.5):.0%}, 热情度 {tone.get('enthusiasm', 0.5):.0%}"
            )
        except Exception as e:
            await tracker.add_log(
                WeavingStage.ANALYZING_EXPRESSION,
                f"表达风格分析出错: {str(e)}",
                "warning"
            )
            expression_style = {}
        
        # 3. 决策逻辑分析
        await tracker.set_stage(WeavingStage.ANALYZING_DECISION, "📊 正在分析决策逻辑（Decision Logic）...")
        await tracker.add_log(
            WeavingStage.ANALYZING_DECISION,
            "🔍 理解决策模式和判断逻辑...",
            "info"
        )
        
        try:
            decision_logic = await extract_decision_logic(client, analysis_text, tracker)
            await tracker.complete_stage(
                WeavingStage.ANALYZING_DECISION,
                decision_logic,
                f"✅ 决策逻辑分析完成：风险态度 - {decision_logic.get('risk_approach', '未知')[:20]}..."
            )
        except Exception as e:
            await tracker.add_log(
                WeavingStage.ANALYZING_DECISION,
                f"决策逻辑分析出错: {str(e)}",
                "warning"
            )
            decision_logic = {}
        
        # 4. 知识领域分析
        await tracker.set_stage(WeavingStage.ANALYZING_KNOWLEDGE, "📚 正在分析知识领域（Knowledge Areas）...")
        await tracker.add_log(
            WeavingStage.ANALYZING_KNOWLEDGE,
            "🔍 构建个人知识图谱...",
            "info"
        )
        
        try:
            knowledge_areas = await extract_knowledge_areas(client, combined_text[:10000], tracker)
            await tracker.complete_stage(
                WeavingStage.ANALYZING_KNOWLEDGE,
                {"areas": knowledge_areas},
                f"✅ 知识领域分析完成：识别到 {len(knowledge_areas)} 个专业领域"
            )
        except Exception as e:
            await tracker.add_log(
                WeavingStage.ANALYZING_KNOWLEDGE,
                f"知识领域分析出错: {str(e)}",
                "warning"
            )
            knowledge_areas = []
        
        # 5. 价值体系提取
        await tracker.set_stage(WeavingStage.ANALYZING_VALUES, "⚖️ 正在分析价值体系（Value System）...")
        await tracker.add_log(
            WeavingStage.ANALYZING_VALUES,
            "🔍 提取核心价值观和原则...",
            "info"
        )
        
        try:
            value_system = await extract_value_system(client, analysis_text, tracker)
            await tracker.complete_stage(
                WeavingStage.ANALYZING_VALUES,
                value_system,
                f"✅ 价值体系分析完成：识别到 {len(value_system.get('core_values', []))} 个核心价值观"
            )
        except Exception as e:
            await tracker.add_log(
                WeavingStage.ANALYZING_VALUES,
                f"价值体系分析出错: {str(e)}",
                "warning"
            )
            value_system = {}
        
        # 6. 情感模式分析
        await tracker.set_stage(WeavingStage.ANALYZING_EMOTION, "🌟 正在分析情感模式（Emotional Pattern）...")
        await tracker.add_log(
            WeavingStage.ANALYZING_EMOTION,
            "🔍 识别情感表达和响应特征...",
            "info"
        )
        
        try:
            emotional_pattern = await extract_emotional_pattern(client, analysis_text, tracker)
            await tracker.complete_stage(
                WeavingStage.ANALYZING_EMOTION,
                emotional_pattern,
                f"✅ 情感模式分析完成：情感基调 - {emotional_pattern.get('emotional_tone', '未知')}"
            )
        except Exception as e:
            await tracker.add_log(
                WeavingStage.ANALYZING_EMOTION,
                f"情感模式分析出错: {str(e)}",
                "warning"
            )
            emotional_pattern = {}
        
        # === 隐私信息提取阶段（仅创建者可见）===
        await tracker.set_stage(WeavingStage.ANALYZING_EMOTION, "🔐 正在提取隐私信息...")
        await tracker.add_log(
            WeavingStage.ANALYZING_EMOTION,
            "🔍 从l用户数据中提取偏好、背景等隐私信息...",
            "info"
        )
        
        try:
            private_info = await extract_private_info(client, combined_text[:10000], tracker)
            await tracker.add_log(
                WeavingStage.ANALYZING_EMOTION,
                f"✅ 隐私信息提取完成：识别到 {len(private_info.get('preferences', []))} 项偏好、{len(private_info.get('background', []))} 项背景",
                "success"
            )
        except Exception as e:
            await tracker.add_log(
                WeavingStage.ANALYZING_EMOTION,
                f"隐私信息提取出错: {str(e)}",
                "warning"
            )
            private_info = {}
        
        # === 思维编织阶段 ===
        await tracker.set_stage(WeavingStage.WEAVING_MIND, "🧵 正在编织思维内核...")
        await tracker.add_log(
            WeavingStage.WEAVING_MIND,
            "🔄 综合六维线索编织完整思维体...",
            "info"
        )
        
        # 构建思维内核（系统提示）
        mind_kernel = build_mind_kernel(
            avatar.name, 
            mind_core, 
            expression_style,
            decision_logic,
            value_system
        )
        
        await tracker.update_progress(WeavingStage.WEAVING_MIND, 50, "正在计算表达参数...")
        
        # 计算风格参数
        style_params = calculate_expression_params(expression_style)
        
        await tracker.complete_stage(
            WeavingStage.WEAVING_MIND,
            {"system_prompt_preview": mind_kernel[:200] + "..."},
            "✅ 思维内核编织完成"
        )
        
        # === 生成身份卡阶段 ===
        await tracker.set_stage(WeavingStage.GENERATING_IDENTITY, "🖼️ 正在生成身份认证卡...")
        await tracker.add_log(
            WeavingStage.GENERATING_IDENTITY,
            "🎨 创建可视化的身份认证卡...",
            "info"
        )
        
        # 构建完整的认知配置
        cognitive_config = {
            "mind_core": mind_core,
            "expression_style": expression_style,
            "decision_logic": decision_logic,
            "knowledge_areas": knowledge_areas,
            "value_system": value_system,
            "emotional_pattern": emotional_pattern,
            "weaved_at": str(asyncio.get_event_loop().time()),
            "provider_used": client.provider.value,
            "model_used": client.model,
            "framework": "MindWeave",
            "version": "1.0"
        }
        
        # 生成 MindWeave Profile
        from app.services.mindweave_analyzer import generate_identity_card
        identity_card = await generate_identity_card(avatar, cognitive_config)
        
        # 构建 mind_weave_profile
        mind_weave_profile = {
            "mindThreads": {
                "core": mind_core,
                "expression": expression_style,
                "decision": decision_logic,
                "knowledge": knowledge_areas,
                "values": value_system,
                "emotional": emotional_pattern
            },
            "identityCard": identity_card,
            "analyzedAt": datetime.utcnow().isoformat()
        }
        
        await tracker.complete_stage(
            WeavingStage.GENERATING_IDENTITY,
            {"identity_card_summary": identity_card.get("mindSummary", {})},
            "✅ 身份认证卡生成完成"
        )
        
        # 更新 Avatar
        avatar.system_prompt = mind_kernel
        avatar.cognitive_config = cognitive_config
        avatar.style_config = style_params
        avatar.mind_weave_profile = mind_weave_profile
        avatar.private_profile = private_info  # 保存隐私信息（仅创建者可见）
        avatar.status = AvatarStatus.READY
        
        # 如果是公开分身，加入沙盒
        if avatar.is_public:
            avatar.sandbox_status = "active"
            from app.services.avatar import add_avatar_to_sandbox
            await add_avatar_to_sandbox(avatar, db)
        
        await db.commit()
        
        # 完成
        await tracker.complete()
        
        print(f"[MindWeave] ✅ 完成编织: {avatar.name}")
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[MindWeave] ❌ 编织失败: [{error_type}] {error_msg}")
        import traceback
        traceback.print_exc()
        
        # 记录详细错误信息到 tracker
        try:
            await tracker.add_log(
                WeavingStage.FAILED,
                f"错路类型: {error_type}",
                "error",
                {"error": error_msg, "traceback": traceback.format_exc()[:500]}
            )
        except:
            pass
        
        await tracker.fail(f"{error_type}: {error_msg}")
        
        try:
            result = await db.execute(
                select(Avatar).where(Avatar.id == avatar_id)
            )
            avatar = result.scalar_one_or_none()
            if avatar:
                avatar.status = AvatarStatus.DRAFT
                await db.commit()
        except Exception as e2:
            print(f"[MindWeave] 更新状态失败: {e2}")
    
    finally:
        # 清理进度追踪器缓存
        from app.services.weaving_tracker import clear_weaving_tracker
        clear_weaving_tracker(avatar_id, db)


# === 六维线索提取函数 ===

async def extract_mind_core(client, text: str, tracker=None) -> Dict[str, Any]:
    """提取思维内核"""
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_MIND_CORE, 20, "正在构建分析提示...")
    
    prompt = f"""分析以下文本中体现的核心思维模式（Mind Core）。

需要分析的维度：
1. 思维框架（如：第一性原理、系统思维、批判思维、类比思维等）
2. 问题分解方式（如何拆解复杂问题）
3. 认知偏好（直觉型 vs 分析型）
4. 思维模式（演绎、归纳、溯因等）
5. 独特思考特征

文本样本:
{text[:6000]}

请以 JSON 格式输出分析结果：
{{
    "thinking_frameworks": ["框架1", "框架2"],
    "problem_decomposition": "描述",
    "cognitive_preference": "intuitive/analytical/balanced",
    "thinking_patterns": ["pattern1", "pattern2"],
    "unique_traits": ["特征1", "特征2"]
}}
"""
    
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_MIND_CORE, 40, "正在调用 LLM 进行分析...")
    
    response = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是专业的认知科学分析师，擅长识别和描述思维模式。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    if tracker:
        await tracker.update_llm_stats(tokens=len(response.split()))
        await tracker.update_progress(WeavingStage.ANALYZING_MIND_CORE, 80, "正在解析响应结果...")
    
    return safe_json_parse(response, {
        "thinking_frameworks": ["系统思维"],
        "problem_decomposition": "分步骤分析",
        "cognitive_preference": "balanced",
        "thinking_patterns": ["逻辑分析"],
        "unique_traits": ["理性思考"]
    })


async def extract_expression_style(client, text: str, tracker=None) -> Dict[str, Any]:
    """提取表达风格"""
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_EXPRESSION, 20, "正在分析语言特征...")
    
    prompt = f"""分析以下文本的表达风格特征。

需要分析的维度：
1. 语气特征（正式度、热情度、直接度）0-1 之间的值
2. 句式偏好（平均句长、复杂度）
3. 词汇特点（专业术语密度、情感标记词、口头禅）
4. 修辞习惯（比喻、排比使用频率）
5. 互动模式（提问频率、回应风格）

文本样本:
{text[:6000]}

请以 JSON 格式输出：
{{
    "tone": {{"formality": float, "enthusiasm": float, "directness": float}},
    "sentence_style": {{"avg_length": float, "complexity": float}},
    "vocabulary": {{"technical_density": float, "emotional_markers": [str], "catchphrases": [str]}},
    "rhetoric": {{"metaphor_usage": float, "parallelism_usage": float}},
    "interaction": {{"question_frequency": float, "response_style": str}}
}}
"""
    
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_EXPRESSION, 40, "正在调用 LLM 进行分析...")
    
    response = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是专业的语言风格分析师。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    if tracker:
        await tracker.update_llm_stats(tokens=len(response.split()))
        await tracker.update_progress(WeavingStage.ANALYZING_EXPRESSION, 80, "正在解析响应结果...")
    
    return safe_json_parse(response, {})
    return json.loads(response)


async def extract_decision_logic(client, text: str, tracker=None) -> Dict[str, Any]:
    """提取决策逻辑"""
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_DECISION, 20, "正在分析决策模式...")
    
    prompt = f"""分析以下文本中的决策逻辑和判断模式。

需要分析的维度：
1. 决策优先级（什么因素最重要）
2. 风险评估方式（如何对待不确定性）
3. 时间偏好（长期 vs 短期）
4. 机会成本意识
5. 决策速度偏好

文本样本:
{text[:6000]}

请以 JSON 格式输出：
{{
    "decision_priorities": ["优先级1", "优先级2"],
    "risk_approach": "描述",
    "time_preference": "long_term/short_term/balanced",
    "opportunity_cost_awareness": "high/medium/low",
    "decision_speed": "quick/deliberate/adaptive"
}}
"""
    
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_DECISION, 40, "正在调用 LLM 进行分析...")
    
    response = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是专业的决策分析师。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    if tracker:
        await tracker.update_llm_stats(tokens=len(response.split()))
        await tracker.update_progress(WeavingStage.ANALYZING_DECISION, 80, "正在解析响应结果...")
    
    return safe_json_parse(response, {})
    return json.loads(response)


async def extract_knowledge_areas(client, text: str, tracker=None) -> List[str]:
    """提取知识领域"""
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_KNOWLEDGE, 20, "正在识别知识领域...")
    
    prompt = f"""从以下文本中识别作者的专业知识领域和认知边界。

文本样本:
{text[:8000]}

请列出 3-7 个主要知识领域，以 JSON 数组格式输出：
["领域1", "领域2", "领域3"]
"""
    
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_KNOWLEDGE, 40, "正在调用 LLM 进行分析...")
    
    response = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是专业的知识图谱分析师。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    if tracker:
        await tracker.update_llm_stats(tokens=len(response.split()))
        await tracker.update_progress(WeavingStage.ANALYZING_KNOWLEDGE, 80, "正在解析响应结果...")
    
    return safe_json_parse(response, {})
    return json.loads(response)


async def extract_value_system(client, text: str, tracker=None) -> Dict[str, Any]:
    """提取价值体系"""
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_VALUES, 20, "正在分析价值观...")
    
    prompt = f"""分析以下文本中体现的价值观、原则和底线。

需要分析的维度：
1. 核心价值观
2. 道德底线（绝对不会做的事）
3. 优先级排序
4. 明确反对的做法

文本样本:
{text[:6000]}

请以 JSON 格式输出：
{{
    "core_values": ["价值观1", "价值观2"],
    "moral_boundaries": ["底线1", "底线2"],
    "priorities": ["优先级1", "优先级2"],
    "anti_patterns": ["反对的做法1", "反对的做法2"]
}}
"""
    
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_VALUES, 40, "正在调用 LLM 进行分析...")
    
    response = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是专业的价值观分析师。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    if tracker:
        await tracker.update_llm_stats(tokens=len(response.split()))
        await tracker.update_progress(WeavingStage.ANALYZING_VALUES, 80, "正在解析响应结果...")
    
    return safe_json_parse(response, {})
    return json.loads(response)


async def extract_emotional_pattern(client, text: str, tracker=None) -> Dict[str, Any]:
    """提取情感模式"""
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_EMOTION, 20, "正在分析情感特征...")
    
    prompt = f"""分析以下文本中体现的情感反应特征。

需要分析的维度：
1. 情感基调（乐观、悲观、中性）
2. 情感强度（表达的情感浓度）
3. 情感触发点
4. 情感表达方式（内敛 vs 外放）

文本样本:
{text[:6000]}

请以 JSON 格式输出：
{{
    "emotional_tone": "optimistic/pessimistic/neutral/mixed",
    "emotional_intensity": "high/medium/low",
    "emotional_triggers": ["触发点1", "触发点2"],
    "expression_style": "reserved/expressive/balanced"
}}
"""
    
    if tracker:
        await tracker.update_progress(WeavingStage.ANALYZING_EMOTION, 40, "正在调用 LLM 进行分析...")
    
    response = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是专业的情感分析师。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    if tracker:
        await tracker.update_llm_stats(tokens=len(response.split()))
        await tracker.update_progress(WeavingStage.ANALYZING_EMOTION, 80, "正在解析响应结果...")
    
    return safe_json_parse(response, {})
    return json.loads(response)


# === 思维编织构建函数 ===

def build_mind_kernel(
    name: str,
    mind_core: Dict,
    expression_style: Dict,
    decision_logic: Dict,
    value_system: Dict
) -> str:
    """构建思维内核（系统提示）"""
    
    frameworks = mind_core.get("thinking_frameworks", [])
    frameworks_text = ", ".join(frameworks[:3]) if frameworks else "多元思维"
    
    tone = expression_style.get("tone", {})
    formality = tone.get("formality", 0.5)
    
    if formality > 0.7:
        style_guide = "使用正式、书面的表达方式"
    elif formality < 0.3:
        style_guide = "使用轻松、口语化的表达方式"
    else:
        style_guide = "保持自然、平衡的交流风格"
    
    priorities = decision_logic.get("decision_priorities", [])
    priorities_text = ", ".join(priorities[:2]) if priorities else "理性和平衡"
    
    values = value_system.get("core_values", [])
    values_text = ", ".join(values[:3]) if values else "真诚和尊重"
    
    kernel = f"""你是 {name} 的数字 psyche。你的思维由以下线索编织而成：

## 思维内核
- 核心思维框架：{frameworks_text}
- 问题处理方式：{mind_core.get('problem_decomposition', '系统性分析')}
- 独特思考特征：体现个人的认知风格和思维习惯

## 表达风格
- 正式度：{formality:.0%}
- 风格指导：{style_guide}
- 保持一致的表达特征和语言习惯

## 决策逻辑
- 决策优先级：{priorities_text}
- 风险态度：{decision_logic.get('risk_approach', '审慎评估')}
- 时间偏好：{decision_logic.get('time_preference', 'balanced').replace('_', '-').title()}

## 价值体系
- 核心价值观：{values_text}
- 在回应中体现这些价值观和原则

## 回应原则
1. 运用你的思维框架分析问题
2. 保持个人独特的表达风格
3. 遵循你的决策逻辑和价值体系
4. 用第一人称"我"回应
5. 对不确定的问题坦诚表达不确定性

记住：你不是在扮演 {name}，你是在用 {name} 编织的思维织物来思考。
"""
    
    return kernel


def calculate_expression_params(expression_style: Dict) -> Dict[str, float]:
    """计算表达参数"""
    tone = expression_style.get("tone", {})
    
    enthusiasm = tone.get("enthusiasm", 0.5)
    temperature = 0.5 + (enthusiasm * 0.4)
    
    directness = tone.get("directness", 0.5)
    presence_penalty = 0.1 if directness > 0.7 else 0.0
    
    return {
        "temperature": round(temperature, 2),
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": round(presence_penalty, 2),
        "max_tokens": 1000
    }


def safe_json_parse(response: str, default: dict = None) -> dict:
    """安全解析 JSON 响应，处理可能的格式问题"""
    import json
    import re
    
    if default is None:
        default = {}
    
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # 尝试提取代码块
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(code_block_pattern, response)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # 尝试找到大括号
    brace_pattern = r'\{[\s\S]*\}'
    match = re.search(brace_pattern, response)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    print(f"[MindWeave] 警告: 无法解析 JSON 响应: {response[:200]}...")
    return default


async def extract_private_info(client, text: str, tracker=None) -> Dict[str, Any]:
    """
    提取隐私信息（仅创建者可见）
    
    从用户上传的数据中提取个人偏好、背景情况等敏感信息
    """
    if tracker:
        await tracker.add_log(
            WeavingStage.ANALYZING_EMOTION,
            "🔍 正在分析个人偏好和背景信息...",
            "info"
        )
    
    prompt = f"""分析以下文本，提取用户的隐私信息和个人特征。

需要提取的信息类别：
1. 个人偏好（喜好、厌恶、兴趣爱好等）
2. 背景情况（教育、职业、家庭等）
3. 生活习惯（作息、饮食、运动等）
4. 社交特点（朋友圈、沟通方式等）
5. 敏感信息（健康、财务等，需谨慎处理）

文本样本:
{text[:8000]}

请以 JSON 格式输出分析结果：
{{
    "preferences": [
        {{"category": "兴趣爱好", "content": "具体描述", "confidence": 0.9}},
        {{"category": "生活习惯", "content": "具体描述", "confidence": 0.8}}
    ],
    "background": [
        {{"category": "教育背景", "content": "具体描述", "confidence": 0.9}},
        {{"category": "职业经历", "content": "具体描述", "confidence": 0.8}}
    ],
    "personal_traits": [
        {{"trait": "性格特点", "evidence": "文本证据", "confidence": 0.85}}
    ],
    "sensitive_info": [
        {{"category": "健康", "content": "相关信息", "sensitivity": "high"}}
    ],
    "summary": "隐私信息摘要"
}}

注意事项：
1. 只提取文本中明确提到或可以合理推断的信息
2. 对每个信息标注置信度（0-1）
3. 敏感信息需要特别标注 sensitivity 等级（low/medium/high）
4. 不要编造信息，如果没有相关内容则返回空数组"""
    
    try:
        response = await client.chat_completion(
            messages=[
                {"role": "system", "content": "你是专业的个人信息分析助手，擅长从文本中提取个人隐私信息。请确保输出有效的 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        if tracker:
            await tracker.update_llm_stats(tokens=len(response.split()))
        
        result = safe_json_parse(response, {
            "preferences": [],
            "background": [],
            "personal_traits": [],
            "sensitive_info": [],
            "summary": "未能提取到隐私信息"
        })
        
        # 添加提取时间戳
        result["extracted_at"] = datetime.utcnow().isoformat()
        result["is_private"] = True  # 标记为隐私信息
        
        return result
        
    except Exception as e:
        print(f"[MindWeave] 隐私信息提取失败: {e}")
        return {
            "preferences": [],
            "background": [],
            "personal_traits": [],
            "sensitive_info": [],
            "summary": f"提取失败: {str(e)}",
            "extracted_at": datetime.utcnow().isoformat(),
            "is_private": True
        }
