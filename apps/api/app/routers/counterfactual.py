"""
反事实模拟 API 路由
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.counterfactual import (
    CounterfactualScenario, SimulationRound, AgentResponse,
    ScenarioType, SimulationPhase
)
from app.services.counterfactual_engine import (
    CounterfactualEngine, run_counterfactual_simulation,
    SCENARIO_PRESETS
)

router = APIRouter(prefix="/counterfactual", tags=["反事实模拟"])


@router.get("/presets")
async def list_presets():
    """获取所有预设场景"""
    return {
        key: {
            "title": preset["title"],
            "description": preset["description"],
            "type": preset["type"],
            "initial_sentiment": preset["initial_sentiment"],
            "initial_heat": preset["initial_heat"]
        }
        for key, preset in SCENARIO_PRESETS.items()
    }


@router.post("/scenarios")
async def create_scenario(
    preset: Optional[str] = None,
    custom_title: Optional[str] = None,
    custom_event: Optional[str] = None,
    avatar_ids: Optional[List[UUID]] = None,
    max_rounds: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的反事实模拟场景
    
    - 使用 preset 选择预设场景（trump_iran, ai_consciousness 等）
    - 或使用 custom_event 创建自定义场景
    """
    try:
        result = await run_counterfactual_simulation(
            db=db,
            user_id=current_user.id,
            preset=preset,
            custom_event=custom_event,
            avatar_ids=avatar_ids,
            max_rounds=max_rounds
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scenario: {str(e)}"
        )


@router.get("/scenarios")
async def list_scenarios(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的反事实模拟列表"""
    query = (
        select(CounterfactualScenario)
        .where(CounterfactualScenario.user_id == current_user.id)
        .order_by(desc(CounterfactualScenario.created_at))
    )
    
    result = await db.execute(query)
    scenarios = result.scalars().all()
    
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "description": s.description,
            "scenario_type": s.scenario_type.value if s.scenario_type else "custom",
            "trigger_event": s.trigger_event,
            "trigger_source": s.trigger_source,
            "status": s.status,
            "max_rounds": s.max_rounds,
            "initial_sentiment": s.initial_sentiment,
            "initial_heat": s.initial_heat,
            "final_summary": s.final_summary,
            "key_findings": s.key_findings,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None
        }
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}")
async def get_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取反事实模拟详情"""
    result = await db.execute(
        select(CounterfactualScenario).where(
            CounterfactualScenario.id == scenario_id,
            CounterfactualScenario.user_id == current_user.id
        )
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # 获取所有轮次
    rounds_result = await db.execute(
        select(SimulationRound)
        .where(SimulationRound.scenario_id == scenario_id)
        .order_by(SimulationRound.round_number)
    )
    rounds = rounds_result.scalars().all()
    
    return {
        "id": str(scenario.id),
        "title": scenario.title,
        "description": scenario.description,
        "trigger_event": scenario.trigger_event,
        "trigger_source": scenario.trigger_source,
        "scenario_type": scenario.scenario_type.value if scenario.scenario_type else "custom",
        "status": scenario.status,
        "max_rounds": scenario.max_rounds,
        "initial_sentiment": scenario.initial_sentiment,
        "initial_heat": scenario.initial_heat,
        "final_summary": scenario.final_summary,
        "key_findings": scenario.key_findings,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "started_at": scenario.started_at.isoformat() if scenario.started_at else None,
        "completed_at": scenario.completed_at.isoformat() if scenario.completed_at else None,
        "rounds": [
            {
                "id": str(r.id),
                "round_number": r.round_number,
                "phase": r.phase.value if r.phase else None,
                "topic": r.topic,
                "topic_keywords": r.topic_keywords,
                "sentiment_score": r.sentiment_score,
                "sentiment_distribution": r.sentiment_distribution,
                "stance_distribution": r.stance_distribution,
                "polarization_index": r.polarization_index,
                "heat_score": r.heat_score,
                "reach_count": r.reach_count,
                "message_count": r.message_count,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in rounds
        ]
    }


@router.get("/scenarios/{scenario_id}/responses")
async def get_scenario_responses(
    scenario_id: UUID,
    round_number: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景中的分身反应/发言"""
    # 验证场景所有权
    result = await db.execute(
        select(CounterfactualScenario).where(
            CounterfactualScenario.id == scenario_id,
            CounterfactualScenario.user_id == current_user.id
        )
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # 构建查询
    query = (
        select(AgentResponse, SimulationRound.round_number)
        .join(SimulationRound, AgentResponse.round_id == SimulationRound.id)
        .where(SimulationRound.scenario_id == scenario_id)
        .order_by(SimulationRound.round_number, AgentResponse.created_at)
    )
    
    if round_number:
        query = query.where(SimulationRound.round_number == round_number)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": str(r.AgentResponse.id),
            "round_number": r.round_number,
            "avatar_id": str(r.AgentResponse.avatar_id),
            "content": r.AgentResponse.content,
            "response_type": r.AgentResponse.response_type.value if r.AgentResponse.response_type else None,
            "sentiment": r.AgentResponse.sentiment,
            "stance": r.AgentResponse.stance,
            "confidence": r.AgentResponse.confidence,
            "thinking_process": r.AgentResponse.thinking_process,
            "influence_score": r.AgentResponse.influence_score,
            "created_at": r.AgentResponse.created_at.isoformat() if r.AgentResponse.created_at else None
        }
        for r in rows
    ]


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除反事实模拟场景"""
    result = await db.execute(
        select(CounterfactualScenario).where(
            CounterfactualScenario.id == scenario_id,
            CounterfactualScenario.user_id == current_user.id
        )
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    await db.delete(scenario)
    await db.commit()
    
    return {"message": "Scenario deleted successfully"}


@router.get("/scenarios/{scenario_id}/timeline")
async def get_scenario_timeline(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景的时间线数据（用于前端可视化）"""
    result = await db.execute(
        select(CounterfactualScenario).where(
            CounterfactualScenario.id == scenario_id,
            CounterfactualScenario.user_id == current_user.id
        )
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # 获取所有轮次及对应的发言
    rounds_result = await db.execute(
        select(SimulationRound)
        .where(SimulationRound.scenario_id == scenario_id)
        .order_by(SimulationRound.round_number)
    )
    rounds = rounds_result.scalars().all()
    
    timeline = []
    for round_data in rounds:
        # 获取该轮的发言
        responses_result = await db.execute(
            select(AgentResponse)
            .where(AgentResponse.round_id == round_data.id)
            .order_by(AgentResponse.created_at)
        )
        responses = responses_result.scalars().all()
        
        timeline.append({
            "round": round_data.round_number,
            "phase": round_data.phase.value if round_data.phase else None,
            "topic": round_data.topic,
            "sentiment_score": round_data.sentiment_score,
            "heat_score": round_data.heat_score,
            "polarization_index": round_data.polarization_index,
            "stance_distribution": round_data.stance_distribution,
            "messages": [
                {
                    "id": str(r.id),
                    "avatar_id": str(r.avatar_id),
                    "content": r.content,
                    "sentiment": r.sentiment,
                    "stance": r.stance,
                    "response_type": r.response_type.value if r.response_type else None,
                    "thinking_process": r.thinking_process
                }
                for r in responses
            ]
        })
    
    return {
        "scenario": {
            "id": str(scenario.id),
            "title": scenario.title,
            "trigger_event": scenario.trigger_event,
            "initial_sentiment": scenario.initial_sentiment,
            "initial_heat": scenario.initial_heat
        },
        "timeline": timeline
    }
