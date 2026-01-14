"""Campaign endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.campaign import Campaign

router = APIRouter()


@router.get("/")
async def list_campaigns(
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List campaigns with optional filtering."""
    query = db.query(Campaign)

    if source:
        query = query.filter(Campaign.source == source)
    if status:
        query = query.filter(Campaign.status == status)

    campaigns = query.offset(offset).limit(limit).all()

    return {
        "campaigns": [
            {
                "id": str(c.id),
                "external_id": c.external_id,
                "name": c.name,
                "source": c.source,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in campaigns
        ],
        "total": query.count(),
    }


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Get campaign by ID."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {
        "id": str(campaign.id),
        "external_id": campaign.external_id,
        "name": campaign.name,
        "source": campaign.source,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }





