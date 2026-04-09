"""
MindWeave - 思维编织服务

基于 MindWeave 理论，提供六维思维线索提取和 psyche 编织服务。
"""
from app.services.mindweave.weaving import (
    start_weaving_task,
    process_weaving,
    # 六维线索提取函数
    extract_mind_core,
    extract_expression_style,
    extract_decision_logic,
    extract_knowledge_areas,
    extract_value_system,
    extract_emotional_pattern,
    # 编织构建函数
    build_mind_kernel,
    calculate_expression_params,
)

__all__ = [
    "start_weaving_task",
    "process_weaving",
    "extract_mind_core",
    "extract_expression_style",
    "extract_decision_logic",
    "extract_knowledge_areas",
    "extract_value_system",
    "extract_emotional_pattern",
    "build_mind_kernel",
    "calculate_expression_params",
]
