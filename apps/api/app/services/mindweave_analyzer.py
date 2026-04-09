"""
MindWeave 思维编织分析服务
使用 LLM 分析用户数据，生成六维思维特征
"""
import json
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.avatar import Avatar
from app.models.user import UserDataSource
from app.core.config import settings
import asyncio


# MindWeave 分析提示词
MINDWEAVE_ANALYSIS_PROMPT = """你是一个专业的认知分析师，擅长通过分析一个人的文字内容来理解其思维方式。

请基于以下用户提供的文本内容，按照 MindWeave 思维编织理论，提取六维思维特征。

MindWeave 六维思维理论：
1. 思维内核 (Mind Core) - 核心认知模式、思考方式
2. 表达风格 (Expression Style) - 语言习惯、修辞特点
3. 决策逻辑 (Decision Logic) - 判断模式、选择偏好
4. 知识领域 (Knowledge Areas) - 知识体系、认知边界
5. 价值体系 (Value System) - 价值观、原则、底线
6. 情感模式 (Emotional Pattern) - 情感反应、情绪表达

请仔细分析文本，提取以下信息并以 JSON 格式返回：

{
  "mindCore": {
    "thinkingFrameworks": ["框架1", "框架2"],  // 常用的思维框架，如"第一性原理"、"系统思维"等
    "problemDecomposition": "描述",  // 如何分解复杂问题
    "cognitivePreference": "描述",  // 认知偏好，如"直觉型"、"分析型"等
    "thinkingPatterns": ["模式1", "模式2"],  // 思维模式特征
    "uniqueTraits": ["特质1", "特质2"]  // 独特思维特质
  },
  "expressionStyle": {
    "tone": {
      "formality": 0.5,  // 正式程度 0-1
      "enthusiasm": 0.5,  // 热情程度 0-1
      "directness": 0.5   // 直接程度 0-1
    },
    "sentenceStyle": {
      "avgLength": 20,  // 平均句长
      "complexity": 0.5  // 句子复杂度 0-1
    },
    "vocabulary": {
      "technicalDensity": 0.3,  // 专业词汇密度 0-1
      "emotionalMarkers": ["词汇1", "词汇2"],  // 情感标记词汇
      "catchphrases": ["口头禅1", "口头禅2"]  // 口头禅/惯用语
    }
  },
  "decisionLogic": {
    "decisionPriorities": ["优先级1", "优先级2"],  // 决策时的优先考虑因素
    "riskApproach": "描述",  // 风险处理方式
    "timePreference": "描述",  // 时间偏好（长期/短期）
    "opportunityCostAwareness": "描述",  // 机会成本意识
    "decisionSpeed": "描述"  // 决策速度特征
  },
  "knowledgeAreas": ["领域1", "领域2", "领域3"],  // 知识领域列表
  "valueSystem": {
    "coreValues": ["价值观1", "价值观2"],  // 核心价值观
    "moralBoundaries": ["底线1", "底线2"],  // 道德底线
    "priorities": ["优先1", "优先2"],  // 人生优先事项
    "antiPatterns": ["反模式1", "反模式2"]  // 明确反对的行为/观念
  },
  "emotionalPattern": {
    "emotionalTone": "描述",  // 情感基调
    "emotionalIntensity": "描述",  // 情感强度特征
    "emotionalTriggers": ["触发点1", "触发点2"],  // 情感触发点
    "expressionStyle": "描述"  // 情感表达方式
  }
}

请确保：
1. 基于文本中的实际证据进行分析
2. 分析结果要具体、有细节，避免空泛
3. 所有数值评分要合理反映文本特征
4. 如果文本内容较少，基于已有内容做合理推断

用户文本内容：
---
{text_content}
---

请只返回 JSON 格式的分析结果，不要包含其他说明文字。"""


async def analyze_mindweave_features(
    avatar: Avatar,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    分析分身的 MindWeave 六维思维特征
    
    1. 读取关联的数据源内容
    2. 使用 LLM 分析生成六维特征
    3. 保存到 avatar.mind_weave_profile
    """
    from app.services.llm.deepseek_client import DeepSeekClient
    
    # 获取数据源内容
    source_texts = []
    
    # 从 used_data_source_ids 获取数据源
    if avatar.used_data_source_ids:
        for ds_id in avatar.used_data_source_ids:
            result = await db.execute(
                select(UserDataSource).where(UserDataSource.id == ds_id)
            )
            ds = result.scalar_one_or_none()
            if ds:
                # 优先使用 extracted_content，否则从 processing_result 中获取
                content = ds.extracted_content
                if not content and ds.processing_result:
                    content = ds.processing_result.get("content") or ds.processing_result.get("text") or ""
                if content:
                    source_texts.append(content)
    
    # 合并文本内容
    combined_text = "\n\n".join(source_texts) if source_texts else avatar.description or ""
    
    if not combined_text or len(combined_text) < 50:
        # 文本太少，使用默认特征
        return generate_default_mindweave_profile(avatar)
    
    # 限制文本长度
    if len(combined_text) > 10000:
        combined_text = combined_text[:10000] + "..."
    
    try:
        # 创建 LLM 客户端
        client = DeepSeekClient(
            api_key=settings.DEEPSEEK_API_KEY,
            model="deepseek-chat"
        )
        
        # 构建消息
        messages = [
            {"role": "system", "content": "你是一个专业的认知分析师。"},
            {"role": "user", "content": MINDWEAVE_ANALYSIS_PROMPT.format(text_content=combined_text)}
        ]
        
        # 调用 LLM
        response = await client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        # 解析 JSON 响应
        # 尝试从响应中提取 JSON
        json_str = extract_json_from_response(response)
        mind_profile = json.loads(json_str)
        
        # 验证并补充缺失的字段
        mind_profile = validate_and_fill_mind_profile(mind_profile)
        
        await client.close()
        
        return mind_profile
        
    except Exception as e:
        print(f"MindWeave analysis failed: {e}")
        # 分析失败时返回默认特征
        return generate_default_mindweave_profile(avatar)


def extract_json_from_response(response: str) -> str:
    """从 LLM 响应中提取 JSON"""
    # 尝试直接解析
    response = response.strip()
    
    # 如果包裹在代码块中，提取内容
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        return response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        return response[start:end].strip()
    
    # 尝试找到 JSON 对象的开始和结束
    start_idx = response.find("{")
    end_idx = response.rfind("}")
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return response[start_idx:end_idx+1]
    
    return response


def validate_and_fill_mind_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """验证并补充缺失的 MindWeave 字段"""
    
    default_profile = {
        "mindCore": {
            "thinkingFrameworks": ["系统思维"],
            "problemDecomposition": "倾向于将复杂问题分解为可管理的部分",
            "cognitivePreference": "平衡型思考者",
            "thinkingPatterns": ["逻辑分析", "经验归纳"],
            "uniqueTraits": ["善于观察"]
        },
        "expressionStyle": {
            "tone": {
                "formality": 0.5,
                "enthusiasm": 0.5,
                "directness": 0.5
            },
            "sentenceStyle": {
                "avgLength": 20,
                "complexity": 0.5
            },
            "vocabulary": {
                "technicalDensity": 0.3,
                "emotionalMarkers": [],
                "catchphrases": []
            }
        },
        "decisionLogic": {
            "decisionPriorities": ["实用性", "效率"],
            "riskApproach": "谨慎评估后决策",
            "timePreference": "注重长期价值",
            "opportunityCostAwareness": "会考虑替代方案",
            "decisionSpeed": "深思熟虑型"
        },
        "knowledgeAreas": ["通用知识"],
        "valueSystem": {
            "coreValues": ["诚信", "责任"],
            "moralBoundaries": ["不伤害他人"],
            "priorities": ["个人成长", "人际关系"],
            "antiPatterns": ["短视行为", "不负责任"]
        },
        "emotionalPattern": {
            "emotionalTone": "平和稳定",
            "emotionalIntensity": "中等",
            "emotionalTriggers": ["不公平对待"],
            "expressionStyle": "倾向于理性表达"
        }
    }
    
    # 递归合并
    def merge_dict(base: Dict, update: Dict) -> Dict:
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dict(result[key], value)
            else:
                result[key] = value
        return result
    
    return merge_dict(default_profile, profile)


def generate_default_mindweave_profile(avatar: Avatar) -> Dict[str, Any]:
    """生成默认的 MindWeave 特征（当数据源不足时）"""
    return {
        "mindCore": {
            "thinkingFrameworks": ["系统思维", "批判性思维"],
            "problemDecomposition": "倾向于将复杂问题分解为可管理的部分，逐步解决",
            "cognitivePreference": "平衡型思考者，兼具直觉与分析",
            "thinkingPatterns": ["逻辑推理", "经验总结", "类比思维"],
            "uniqueTraits": ["善于观察细节", "追求理解本质"]
        },
        "expressionStyle": {
            "tone": {
                "formality": 0.6,
                "enthusiasm": 0.5,
                "directness": 0.6
            },
            "sentenceStyle": {
                "avgLength": 18,
                "complexity": 0.5
            },
            "vocabulary": {
                "technicalDensity": 0.3,
                "emotionalMarkers": ["确实", "其实", "我觉得"],
                "catchphrases": []
            }
        },
        "decisionLogic": {
            "decisionPriorities": ["实用性", "长期影响", "道德考量"],
            "riskApproach": "谨慎评估风险后行动，避免冲动决策",
            "timePreference": "注重长期价值，兼顾短期需求",
            "opportunityCostAwareness": "会主动考虑替代方案和机会成本",
            "decisionSpeed": "深思熟虑型，重要决策需要时间"
        },
        "knowledgeAreas": ["通用知识", "生活智慧", "专业领域知识"],
        "valueSystem": {
            "coreValues": ["诚信", "责任", "成长", "尊重"],
            "moralBoundaries": ["不伤害他人", "不违背承诺", "不投机取巧"],
            "priorities": ["个人成长", "人际关系", "工作成就", "生活质量"],
            "antiPatterns": ["短视行为", "不负责任", "虚伪欺骗", "固步自封"]
        },
        "emotionalPattern": {
            "emotionalTone": "平和稳定，偶尔波动",
            "emotionalIntensity": "中等强度，能够控制",
            "emotionalTriggers": ["不公平对待", "被误解", "目标受阻"],
            "expressionStyle": "倾向于理性表达情感，避免过度情绪化"
        }
    }


async def generate_identity_card(
    avatar: Avatar,
    mind_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    生成分身的身份卡信息
    
    基于 MindWeave 特征，生成一个易于展示的身份卡
    支持驼峰命名（camelCase）和下划线命名（snake_case）两种格式
    """
    # 辅助函数：安全获取字段（支持驼峰和下划线两种命名）
    def get_field(data: dict, camel_key: str, snake_key: str, default=None):
        return data.get(camel_key, data.get(snake_key, default))
    
    # 提取各模块数据（兼容两种命名格式）
    mind_core = get_field(mind_profile, "mindCore", "mind_core", {})
    expression_style = get_field(mind_profile, "expressionStyle", "expression_style", {})
    decision_logic = get_field(mind_profile, "decisionLogic", "decision_logic", {})
    emotional_pattern = get_field(mind_profile, "emotionalPattern", "emotional_pattern", {})
    value_system = get_field(mind_profile, "valueSystem", "value_system", {})
    knowledge_areas = get_field(mind_profile, "knowledgeAreas", "knowledge_areas", [])
    
    # 提取关键特征用于身份卡展示
    identity_card = {
        "basicInfo": {
            "name": avatar.name,
            "description": avatar.description or "一个基于 MindWeave 理论构建的数字分身",
            "type": avatar.avatar_type.value if hasattr(avatar.avatar_type, 'value') else str(avatar.avatar_type),
            "createdAt": avatar.created_at.isoformat() if avatar.created_at else None,
        },
        "mindSummary": {
            "thinkingStyle": mind_core.get("cognitivePreference", mind_core.get("cognitive_preference", "平衡型")),
            "expressionStyle": describe_expression_style(expression_style),
            "decisionStyle": decision_logic.get("riskApproach", decision_logic.get("risk_approach", "谨慎型")),
            "emotionalTone": emotional_pattern.get("emotionalTone", emotional_pattern.get("emotional_tone", "平和")),
        },
        "keyTraits": extract_key_traits(mind_profile),
        "knowledgeTags": knowledge_areas[:6] if isinstance(knowledge_areas, list) else [],
        "coreValues": value_system.get("coreValues", value_system.get("core_values", []))[:4],
        "stats": {
            "formality": expression_style.get("tone", {}).get("formality", 0.5),
            "enthusiasm": expression_style.get("tone", {}).get("enthusiasm", 0.5),
            "directness": expression_style.get("tone", {}).get("directness", 0.5),
            "complexity": expression_style.get("sentenceStyle", expression_style.get("sentence_style", {})).get("complexity", 0.5),
        }
    }
    
    return identity_card


def describe_expression_style(expression: Dict[str, Any]) -> str:
    """描述表达风格"""
    tone = expression.get("tone", {})
    formality = tone.get("formality", 0.5)
    directness = tone.get("directness", 0.5)
    
    style_parts = []
    
    if formality > 0.7:
        style_parts.append("正式")
    elif formality < 0.3:
        style_parts.append("随意")
    else:
        style_parts.append("自然")
    
    if directness > 0.7:
        style_parts.append("直接")
    elif directness < 0.3:
        style_parts.append("委婉")
    else:
        style_parts.append("适中")
    
    return "、".join(style_parts)


def extract_key_traits(mind_profile: Dict[str, Any]) -> List[str]:
    """提取关键特质标签（兼容驼峰命名和下划线命名）"""
    traits = []
    
    # 辅助函数：安全获取字段
    def get_field(data: dict, camel_key: str, snake_key: str, default=None):
        return data.get(camel_key, data.get(snake_key, default))
    
    # 从思维内核提取
    mind_core = get_field(mind_profile, "mindCore", "mind_core", {})
    traits.extend(mind_core.get("uniqueTraits", mind_core.get("unique_traits", []))[:2])
    
    # 从决策逻辑提取
    decision = get_field(mind_profile, "decisionLogic", "decision_logic", {})
    decision_speed = decision.get("decisionSpeed", decision.get("decision_speed", ""))
    if "深思熟虑" in decision_speed:
        traits.append("深思熟虑")
    elif "果断" in decision_speed:
        traits.append("果断决策")
    
    # 从情感模式提取
    emotional = get_field(mind_profile, "emotionalPattern", "emotional_pattern", {})
    intensity = emotional.get("emotionalIntensity", emotional.get("emotional_intensity", ""))
    if "理性" in emotional.get("expressionStyle", emotional.get("expression_style", "")):
        traits.append("理性克制")
    
    # 从价值观提取
    values = get_field(mind_profile, "valueSystem", "value_system", {})
    priorities = values.get("priorities", [])
    if priorities:
        traits.append(f"重视{priorities[0]}")
    
    return list(set(traits))[:5]  # 去重并限制数量
