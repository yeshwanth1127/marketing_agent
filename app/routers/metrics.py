"""Metrics endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta
from app.database import get_db
from app.models.metrics import DailyMetric, WeeklyMetric

router = APIRouter()


@router.get("/daily")
async def get_daily_metrics(
    campaign_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    source: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get daily metrics with optional filtering."""
    query = db.query(DailyMetric)

    if campaign_id:
        query = query.filter(DailyMetric.campaign_id == campaign_id)
    if start_date:
        query = query.filter(DailyMetric.date >= start_date)
    if end_date:
        query = query.filter(DailyMetric.date <= end_date)
    if source:
        query = query.filter(DailyMetric.source == source)

    metrics = query.order_by(DailyMetric.date.desc()).limit(limit).all()

    return {
        "metrics": [
            {
                "id": str(m.id),
                "date": m.date.isoformat() if m.date else None,
                "campaign_id": str(m.campaign_id),
                "source": m.source,
                "impressions": m.impressions,
                "clicks": m.clicks,
                "spend": float(m.spend) if m.spend else 0,
                "conversions": m.conversions,
                "revenue": float(m.revenue) if m.revenue else 0,
            }
            for m in metrics
        ],
        "total": query.count(),
    }


@router.get("/weekly")
async def get_weekly_metrics(
    campaign_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    source: Optional[str] = None,
    limit: int = 52,
    db: Session = Depends(get_db),
):
    """Get weekly metrics with optional filtering."""
    query = db.query(WeeklyMetric)

    if campaign_id:
        query = query.filter(WeeklyMetric.campaign_id == campaign_id)
    if start_date:
        query = query.filter(WeeklyMetric.week_start >= start_date)
    if end_date:
        query = query.filter(WeeklyMetric.week_start <= end_date)
    if source:
        query = query.filter(WeeklyMetric.source == source)

    metrics = query.order_by(WeeklyMetric.week_start.desc()).limit(limit).all()

    return {
        "metrics": [
            {
                "id": str(m.id),
                "week_start": m.week_start.isoformat() if m.week_start else None,
                "campaign_id": str(m.campaign_id),
                "source": m.source,
                "impressions": m.impressions,
                "clicks": m.clicks,
                "spend": float(m.spend) if m.spend else 0,
                "conversions": m.conversions,
                "revenue": float(m.revenue) if m.revenue else 0,
                "roas": float(m.roas) if m.roas else None,
                "ctr": float(m.ctr) if m.ctr else None,
                "cpc": float(m.cpc) if m.cpc else None,
            }
            for m in metrics
        ],
        "total": query.count(),
    }





