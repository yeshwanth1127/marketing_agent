"""Data ingestion service for normalizing and storing marketing data."""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.campaign import Campaign
from app.models.metrics import DailyMetric
import logging

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for ingesting and normalizing marketing data from various sources."""

    def __init__(self, db: Session):
        """Initialize the ingestion service with a database session."""
        self.db = db

    def normalize_metric_data(self, raw_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Normalize raw metric data to canonical format.

        Args:
            raw_data: Raw data from source (Meta Ads, GA4, etc.)
            source: Source identifier ('meta_ads', 'ga4', etc.)

        Returns:
            Normalized data dictionary
        """
        # Extract common fields
        normalized = {
            "external_id": str(raw_data.get("external_id", "")),
            "campaign_name": str(raw_data.get("campaign", "") or raw_data.get("campaign_name", "")),
            "date": self._parse_date(raw_data.get("date") or raw_data.get("date_start")),
            "impressions": int(raw_data.get("impressions", 0) or 0),
            "clicks": int(raw_data.get("clicks", 0) or 0),
            "spend": Decimal(str(raw_data.get("spend", 0) or raw_data.get("cost", 0))),
            "conversions": int(raw_data.get("conversions", 0) or raw_data.get("purchases", 0) or 0),
            "revenue": Decimal(str(raw_data.get("revenue", 0) or raw_data.get("value", 0))),
            "source": source,
            "status": raw_data.get("status", "active"),
        }

        # Validate required fields
        if not normalized["external_id"]:
            raise ValueError(f"external_id is required for source {source}")
        if not normalized["campaign_name"]:
            raise ValueError(f"campaign_name is required for source {source}")
        if not normalized["date"]:
            raise ValueError(f"date is required for source {source}")

        return normalized

    def upsert_campaign(self, normalized_data: Dict[str, Any]) -> Campaign:
        """
        Upsert a campaign (create if not exists, update if exists).

        Args:
            normalized_data: Normalized data dictionary

        Returns:
            Campaign model instance
        """
        external_id = normalized_data["external_id"]
        source = normalized_data["source"]

        # Find existing campaign
        campaign = (
            self.db.query(Campaign)
            .filter(and_(Campaign.external_id == external_id, Campaign.source == source))
            .first()
        )

        if campaign:
            # Update existing campaign
            campaign.name = normalized_data["campaign_name"]
            campaign.status = normalized_data.get("status", campaign.status)
            campaign.updated_at = datetime.now()
            logger.info(f"Updated campaign: {campaign.name} (ID: {campaign.id})")
        else:
            # Create new campaign
            campaign = Campaign(
                external_id=external_id,
                name=normalized_data["campaign_name"],
                source=source,
                status=normalized_data.get("status", "active"),
            )
            self.db.add(campaign)
            self.db.flush()  # Flush to get the ID
            logger.info(f"Created campaign: {campaign.name} (ID: {campaign.id})")

        return campaign

    def upsert_daily_metric(self, normalized_data: Dict[str, Any], campaign: Campaign) -> DailyMetric:
        """
        Upsert a daily metric (create if not exists, update if exists).

        Args:
            normalized_data: Normalized data dictionary
            campaign: Campaign model instance

        Returns:
            DailyMetric model instance
        """
        metric_date = normalized_data["date"]
        source = normalized_data["source"]

        # Find existing metric
        daily_metric = (
            self.db.query(DailyMetric)
            .filter(
                and_(
                    DailyMetric.date == metric_date,
                    DailyMetric.campaign_id == campaign.id,
                    DailyMetric.source == source,
                )
            )
            .first()
        )

        if daily_metric:
            # Update existing metric
            daily_metric.impressions = normalized_data["impressions"]
            daily_metric.clicks = normalized_data["clicks"]
            daily_metric.spend = normalized_data["spend"]
            daily_metric.conversions = normalized_data["conversions"]
            daily_metric.revenue = normalized_data["revenue"]
            logger.info(f"Updated daily metric for {campaign.name} on {metric_date}")
        else:
            # Create new metric
            daily_metric = DailyMetric(
                date=metric_date,
                campaign_id=campaign.id,
                source=source,
                impressions=normalized_data["impressions"],
                clicks=normalized_data["clicks"],
                spend=normalized_data["spend"],
                conversions=normalized_data["conversions"],
                revenue=normalized_data["revenue"],
            )
            self.db.add(daily_metric)
            logger.info(f"Created daily metric for {campaign.name} on {metric_date}")

        return daily_metric

    def ingest_metric(self, raw_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Ingest a single metric record (normalize, upsert campaign, upsert metric).

        Args:
            raw_data: Raw data from source
            source: Source identifier

        Returns:
            Dictionary with campaign and metric information
        """
        try:
            # Normalize data
            normalized = self.normalize_metric_data(raw_data, source)

            # Upsert campaign
            campaign = self.upsert_campaign(normalized)

            # Upsert daily metric
            daily_metric = self.upsert_daily_metric(normalized, campaign)

            # Commit transaction
            self.db.commit()

            return {
                "success": True,
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "metric_id": str(daily_metric.id),
                "date": str(daily_metric.date),
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error ingesting metric: {str(e)}", exc_info=True)
            raise

    def ingest_batch(self, raw_data_list: list[Dict[str, Any]], source: str) -> Dict[str, Any]:
        """
        Ingest multiple metric records in a batch.

        Args:
            raw_data_list: List of raw data dictionaries
            source: Source identifier

        Returns:
            Summary dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0, "errors": []}

        for raw_data in raw_data_list:
            try:
                self.ingest_metric(raw_data, source)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"data": raw_data, "error": str(e)})
                logger.error(f"Failed to ingest metric: {str(e)}")

        return results

    def _parse_date(self, date_value: Any) -> date:
        """
        Parse date from various formats.

        Args:
            date_value: Date value (string, date, datetime, etc.)

        Returns:
            date object
        """
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_value}")
        raise ValueError(f"Invalid date type: {type(date_value)}")

