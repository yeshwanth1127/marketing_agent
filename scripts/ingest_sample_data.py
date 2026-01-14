"""Script to ingest sample data for manual testing.

This script creates sample marketing data in the canonical format
and ingests it into the database. Useful for testing the ingestion
pipeline without real API connections.

Usage:
    python scripts/ingest_sample_data.py
"""

import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.ingestion import DataIngestionService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_meta_ads_data(num_days: int = 7) -> list[dict]:
    """Generate sample Meta Ads data for testing."""
    base_date = date.today() - timedelta(days=num_days)
    campaigns = [
        {"external_id": "meta_ads_123456", "campaign": "Summer Sale Campaign", "status": "active"},
        {"external_id": "meta_ads_789012", "campaign": "Product Launch", "status": "active"},
        {"external_id": "meta_ads_345678", "campaign": "Retargeting Campaign", "status": "paused"},
    ]

    sample_data = []
    for i in range(num_days):
        current_date = base_date + timedelta(days=i)
        for campaign in campaigns:
            # Generate realistic-ish variation in metrics
            base_impressions = 10000 + (i * 500)
            base_clicks = 300 + (i * 10)
            base_spend = 500.0 + (i * 20.0)
            base_conversions = 10 + (i // 2)
            base_revenue = 2000.0 + (i * 100.0)

            sample_data.append(
                {
                    "external_id": campaign["external_id"],
                    "campaign": campaign["campaign"],
                    "date": current_date.isoformat(),
                    "impressions": base_impressions,
                    "clicks": base_clicks,
                    "spend": base_spend,
                    "conversions": base_conversions,
                    "revenue": base_revenue,
                    "status": campaign["status"],
                }
            )

    return sample_data


def generate_sample_ga4_data(num_days: int = 7) -> list[dict]:
    """Generate sample GA4 data for testing."""
    base_date = date.today() - timedelta(days=num_days)
    campaigns = [
        {"external_id": "ga4_source_1", "campaign": "Organic Search", "status": "active"},
        {"external_id": "ga4_source_2", "campaign": "Paid Search", "status": "active"},
        {"external_id": "ga4_source_3", "campaign": "Social Media", "status": "active"},
    ]

    sample_data = []
    for i in range(num_days):
        current_date = base_date + timedelta(days=i)
        for campaign in campaigns:
            # GA4 format uses different field names
            base_sessions = 5000 + (i * 200)
            base_clicks = base_sessions  # Sessions approximate clicks
            base_cost = 300.0 + (i * 15.0)
            base_purchases = 8 + (i // 2)
            base_value = 1500.0 + (i * 80.0)

            sample_data.append(
                {
                    "external_id": campaign["external_id"],
                    "campaign_name": campaign["campaign"],
                    "date_start": current_date.isoformat(),
                    "impressions": base_sessions * 2,  # Estimate impressions
                    "clicks": base_clicks,
                    "cost": base_cost,
                    "purchases": base_purchases,
                    "value": base_value,
                    "status": campaign["status"],
                }
            )

    return sample_data


def main():
    """Main function to ingest sample data."""
    db: Session = SessionLocal()
    try:
        ingestion_service = DataIngestionService(db)

        logger.info("Generating sample Meta Ads data...")
        meta_ads_data = generate_sample_meta_ads_data(num_days=7)
        logger.info(f"Generated {len(meta_ads_data)} Meta Ads records")

        logger.info("Ingesting Meta Ads data...")
        meta_results = ingestion_service.ingest_batch(meta_ads_data, source="meta_ads")
        logger.info(f"Meta Ads ingestion: {meta_results['success']} successful, {meta_results['failed']} failed")

        if meta_results["failed"] > 0:
            logger.error(f"Errors: {meta_results['errors']}")

        logger.info("Generating sample GA4 data...")
        ga4_data = generate_sample_ga4_data(num_days=7)
        logger.info(f"Generated {len(ga4_data)} GA4 records")

        logger.info("Ingesting GA4 data...")
        ga4_results = ingestion_service.ingest_batch(ga4_data, source="ga4")
        logger.info(f"GA4 ingestion: {ga4_results['success']} successful, {ga4_results['failed']} failed")

        if ga4_results["failed"] > 0:
            logger.error(f"Errors: {ga4_results['errors']}")

        logger.info("Sample data ingestion completed!")
        logger.info(f"Total: {meta_results['success'] + ga4_results['success']} records ingested")

    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

