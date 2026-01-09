"""Agent execution endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models.agent import AgentRun
from app.services.agent_service import AgentService

router = APIRouter()


class RunWeeklyRequest(BaseModel):
    """Request model for weekly agent run."""

    days_back: int = 30
    comparison_days: int = 7


class RunWeeklyResponse(BaseModel):
    """Response model for weekly agent run."""

    run_id: str
    status: str
    started_at: datetime
    message: str


@router.post("/run-weekly", response_model=RunWeeklyResponse)
async def run_weekly_agent(
    request: RunWeeklyRequest = RunWeeklyRequest(),
    db: Session = Depends(get_db),
):
    """
    Trigger a weekly agent run.
    This endpoint is called by n8n after data ingestion.
    """
    try:
        agent_service = AgentService(db)
        run = agent_service.run_weekly_analysis(
            days_back=request.days_back,
            comparison_days=request.comparison_days,
        )
        return RunWeeklyResponse(
            run_id=str(run.id),
            status=run.status,
            started_at=run.started_at,
            message="Weekly agent run started successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start agent run: {str(e)}")


@router.get("/runs/{run_id}")
async def get_agent_run(run_id: str, db: Session = Depends(get_db)):
    """Get agent run details by ID."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return {
        "id": str(run.id),
        "run_type": run.run_type,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "input_params": run.input_params,
        "output": run.output,
        "error_message": run.error_message,
    }


@router.get("/runs")
async def list_agent_runs(
    limit: int = 10,
    offset: int = 0,
    run_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List agent runs with optional filtering."""
    query = db.query(AgentRun)

    if run_type:
        query = query.filter(AgentRun.run_type == run_type)
    if status:
        query = query.filter(AgentRun.status == status)

    runs = query.order_by(AgentRun.started_at.desc()).offset(offset).limit(limit).all()

    return {
        "runs": [
            {
                "id": str(run.id),
                "run_type": run.run_type,
                "status": run.status,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
            }
            for run in runs
        ],
        "total": query.count(),
    }

