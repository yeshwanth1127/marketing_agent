"""API endpoints for data ingestion from external sources."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List
from app.database import get_db
from app.services.ingestion import DataIngestionService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class IngestionRequest(BaseModel):
    """Request model for data ingestion."""

    raw_data: Dict[str, Any]
    source: str


class BatchIngestionRequest(BaseModel):
    """Request model for batch data ingestion."""

    raw_data_list: List[Dict[str, Any]]
    source: str


class IngestionResponse(BaseModel):
    """Response model for data ingestion."""

    success: bool
    campaign_id: str = None
    campaign_name: str = None
    metric_id: str = None
    date: str = None
    error: str = None


class BatchIngestionResponse(BaseModel):
    """Response model for batch data ingestion."""

    success: int
    failed: int
    errors: List[Dict[str, Any]] = []


@router.post("/upsert", response_model=IngestionResponse)
async def upsert_metric(
    request: IngestionRequest, db: Session = Depends(get_db)
) -> IngestionResponse:
    """
    Upsert a single metric record.

    This endpoint is called by n8n workflows to ingest data from external sources.
    """
    try:
        ingestion_service = DataIngestionService(db)
        result = ingestion_service.ingest_metric(request.raw_data, request.source)

        return IngestionResponse(
            success=True,
            campaign_id=result["campaign_id"],
            campaign_name=result["campaign_name"],
            metric_id=result["metric_id"],
            date=result["date"],
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error ingesting metric: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/upsert-batch", response_model=BatchIngestionResponse)
async def upsert_batch(
    request: BatchIngestionRequest, db: Session = Depends(get_db)
) -> BatchIngestionResponse:
    """
    Upsert multiple metric records in a batch.

    This endpoint is called by n8n workflows to ingest multiple records at once.
    """
    try:
        ingestion_service = DataIngestionService(db)
        results = ingestion_service.ingest_batch(request.raw_data_list, request.source)

        return BatchIngestionResponse(
            success=results["success"],
            failed=results["failed"],
            errors=results.get("errors", []),
        )
    except Exception as e:
        logger.error(f"Error ingesting batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

