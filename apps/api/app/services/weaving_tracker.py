"""
编织进度追踪服务
管理 MindWeave 编织过程的实时进度追踪和 WebSocket 推送
"""
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.weaving_progress import WeavingProgress, WeavingStage, WeavingSession
from app.core.websocket import manager


class WeavingTracker:
    """编织进度追踪器"""
    
    def __init__(self, avatar_id: str, db: AsyncSession):
        self.avatar_id = avatar_id
        self.db = db
        self.progress: Optional[WeavingProgress] = None
        self._callbacks: list[Callable] = []
    
    async def initialize(self) -> WeavingProgress:
        """初始化进度记录"""
        # 检查是否已有进度记录
        result = await self.db.execute(
            select(WeavingProgress).where(WeavingProgress.avatar_id == self.avatar_id)
        )
        self.progress = result.scalar_one_or_none()
        
        if not self.progress:
            # 创建新的进度记录
            self.progress = WeavingProgress(
                avatar_id=UUID(self.avatar_id),
                current_stage=WeavingStage.PREPARING,
                overall_progress=0.0,
                stage_progress={},
                logs=[],
                intermediate_results={},
                llm_stats={"calls_count": 0, "tokens_used": 0, "provider": "", "model": ""}
            )
            self.db.add(self.progress)
            await self.db.commit()
        
        return self.progress
    
    async def set_stage(self, stage: WeavingStage, message: str = None):
        """设置当前阶段"""
        if not self.progress:
            await self.initialize()
        
        self.progress.current_stage = stage
        
        if message:
            self.progress.add_log(stage, message, "info")
        
        # 更新阶段进度
        self.progress.update_stage_progress(stage, 0, "running")
        
        await self.db.commit()
        await self._notify()
    
    async def update_progress(self, stage: WeavingStage, progress: float, message: str = None):
        """更新阶段进度"""
        if not self.progress:
            await self.initialize()
        
        self.progress.update_stage_progress(stage, progress, "running")
        
        if message:
            self.progress.add_log(stage, message, "info")
        
        await self.db.commit()
        await self._notify()
    
    async def complete_stage(self, stage: WeavingStage, result: Dict = None, message: str = None):
        """完成阶段"""
        if not self.progress:
            await self.initialize()
        
        self.progress.update_stage_progress(stage, 100, "completed")
        
        if result:
            self.progress.set_intermediate_result(stage, result)
        
        if message:
            self.progress.add_log(stage, message, "success")
        else:
            self.progress.add_log(stage, f"{stage.value} 完成", "success")
        
        await self.db.commit()
        await self._notify()
    
    async def add_log(self, stage: WeavingStage, message: str, log_type: str = "info", metadata: Dict = None):
        """添加日志"""
        if not self.progress:
            await self.initialize()
        
        self.progress.add_log(stage, message, log_type, metadata)
        await self.db.commit()
        await self._notify()
    
    async def set_text_preview(self, text: str, max_length: int = 500):
        """设置当前文本预览"""
        if not self.progress:
            await self.initialize()
        
        preview = text[:max_length] + "..." if len(text) > max_length else text
        self.progress.current_text_preview = preview
        await self.db.commit()
    
    async def update_llm_stats(self, provider: str = None, model: str = None, tokens: int = 0):
        """更新 LLM 调用统计"""
        if not self.progress:
            await self.initialize()
        
        if self.progress.llm_stats is None:
            self.progress.llm_stats = {"calls_count": 0, "tokens_used": 0, "provider": "", "model": ""}
        
        self.progress.llm_stats["calls_count"] += 1
        self.progress.llm_stats["tokens_used"] += tokens
        
        if provider:
            self.progress.llm_stats["provider"] = provider
        if model:
            self.progress.llm_stats["model"] = model
        
        await self.db.commit()
    
    async def complete(self):
        """标记编织完成"""
        if not self.progress:
            await self.initialize()
        
        self.progress.current_stage = WeavingStage.COMPLETED
        self.progress.overall_progress = 100.0
        self.progress.completed_at = datetime.utcnow()
        self.progress.add_log(WeavingStage.COMPLETED, "🎉 MindWeave 编织完成！数字分身已准备就绪", "success")
        
        await self.db.commit()
        await self._notify()
    
    async def fail(self, error_message: str):
        """标记编织失败"""
        if not self.progress:
            await self.initialize()
        
        self.progress.current_stage = WeavingStage.FAILED
        self.progress.error_message = error_message
        self.progress.add_log(WeavingStage.FAILED, f"❌ 编织失败: {error_message}", "error")
        
        await self.db.commit()
        await self._notify()
    
    async def _notify(self):
        """通知所有监听者（WebSocket 推送）"""
        if not self.progress:
            return
        
        data = self.progress.to_dict()
        
        # WebSocket 推送
        try:
            await manager.broadcast_to_avatar_weaving(self.avatar_id, data)
        except Exception as e:
            print(f"[WeavingTracker] WebSocket push error: {e}")
        
        # 回调函数
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                print(f"[WeavingTracker] Callback error: {e}")
    
    def on_update(self, callback: Callable):
        """注册更新回调"""
        self._callbacks.append(callback)
    
    def get_progress(self) -> Optional[WeavingProgress]:
        """获取当前进度"""
        return self.progress


# 全局进度追踪器缓存
_weaving_trackers: Dict[str, WeavingTracker] = {}


def get_weaving_tracker(avatar_id: str, db: AsyncSession) -> WeavingTracker:
    """获取或创建编织进度追踪器"""
    cache_key = f"{avatar_id}_{id(db)}"
    if cache_key not in _weaving_trackers:
        _weaving_trackers[cache_key] = WeavingTracker(avatar_id, db)
    return _weaving_trackers[cache_key]


def clear_weaving_tracker(avatar_id: str, db: AsyncSession):
    """清除编织进度追踪器"""
    cache_key = f"{avatar_id}_{id(db)}"
    if cache_key in _weaving_trackers:
        del _weaving_trackers[cache_key]


# 帮助函数和常量
STAGE_DESCRIPTIONS = {
    WeavingStage.PREPARING: {
        "title": "准备阶段",
        "description": "读取和准备用户数据源",
        "icon": "📤"
    },
    WeavingStage.EXTRACTING_TEXT: {
        "title": "文本提取",
        "description": "从上传文件中提取可分析的文本内容",
        "icon": "📝"
    },
    WeavingStage.ANALYZING_MIND_CORE: {
        "title": "分析思维内核",
        "description": "识别核心思维框架和认知偏好",
        "icon": "🧠"
    },
    WeavingStage.ANALYZING_EXPRESSION: {
        "title": "分析表达风格",
        "description": "提取语言习惯和表达特征",
        "icon": "💬"
    },
    WeavingStage.ANALYZING_DECISION: {
        "title": "分析决策逻辑",
        "description": "理解决策模式和判断逻辑",
        "icon": "📊"
    },
    WeavingStage.ANALYZING_KNOWLEDGE: {
        "title": "分析知识领域",
        "description": "构建个人知识图谱",
        "icon": "📚"
    },
    WeavingStage.ANALYZING_VALUES: {
        "title": "分析价值体系",
        "description": "提取核心价值观和原则",
        "icon": "⚖️"
    },
    WeavingStage.ANALYZING_EMOTION: {
        "title": "分析情感模式",
        "description": "识别情感表达和响应特征",
        "icon": "🌟"
    },
    WeavingStage.WEAVING_MIND: {
        "title": "编织思维内核",
        "description": "综合六维线索编织完整思维体",
        "icon": "🧵"
    },
    WeavingStage.GENERATING_IDENTITY: {
        "title": "生成身份卡",
        "description": "创建可视化的身份认证卡",
        "icon": "🖼️"
    },
    WeavingStage.COMPLETED: {
        "title": "编织完成",
        "description": "数字分身已准备就绪",
        "icon": "✅"
    },
    WeavingStage.FAILED: {
        "title": "编织失败",
        "description": "过程中发生错误",
        "icon": "❌"
    }
}


def get_stage_info(stage: WeavingStage) -> Dict[str, str]:
    """获取阶段信息"""
    return STAGE_DESCRIPTIONS.get(stage, {
        "title": stage.value,
        "description": "",
        "icon": "🔄"
    })
