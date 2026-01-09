"""Analytics Agent - Analyzes performance data and identifies patterns."""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.agent import Insight
from app.models.metrics import DailyMetric
from datetime import datetime, timedelta
from uuid import uuid4


class AnalyticsAgent:
    """Analytics Agent for performance analysis."""

    def __init__(self, db: Session):
        self.db = db

    def analyze(
        self,
        run_id: str,
        days_back: int = 30,
        comparison_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Analyze campaign performance and generate insights.
        
        Returns list of insight dictionaries.
        """
        # Calculate date ranges
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days_back)
        comparison_start = end_date - timedelta(days=comparison_days)

        # Get metrics for current period
        current_metrics = self._get_aggregated_metrics(
            start_date=comparison_start,
            end_date=end_date,
        )

        # Get metrics for previous period
        previous_start = comparison_start - timedelta(days=comparison_days)
        previous_metrics = self._get_aggregated_metrics(
            start_date=previous_start,
            end_date=comparison_start,
        )

        # Compare and generate insights
        insights = self._compare_periods(
            current_metrics=current_metrics,
            previous_metrics=previous_metrics,
            run_id=run_id,
        )

        # Save insights to database
        for insight_data in insights:
            insight = Insight(
                id=uuid4(),
                agent_run_id=run_id,
                insight_type=insight_data["type"],
                campaign_id=insight_data["campaign_id"],
                metric=insight_data["metric"],
                change_percent=insight_data.get("change_percent"),
                description=insight_data.get("description"),
                severity=insight_data.get("severity", "medium"),
            )
            self.db.add(insight)

        self.db.commit()

        return insights

    def _get_aggregated_metrics(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> Dict[str, Dict[str, Any]]:
        """Get aggregated metrics by campaign for a date range."""
        metrics = (
            self.db.query(DailyMetric)
            .filter(
                DailyMetric.date >= start_date,
                DailyMetric.date < end_date,
            )
            .all()
        )

        # Aggregate by campaign
        aggregated = {}
        for metric in metrics:
            campaign_id = str(metric.campaign_id)
            if campaign_id not in aggregated:
                aggregated[campaign_id] = {
                    "campaign_id": campaign_id,
                    "impressions": 0,
                    "clicks": 0,
                    "spend": 0.0,
                    "conversions": 0,
                    "revenue": 0.0,
                }

            aggregated[campaign_id]["impressions"] += metric.impressions or 0
            aggregated[campaign_id]["clicks"] += metric.clicks or 0
            aggregated[campaign_id]["spend"] += float(metric.spend or 0)
            aggregated[campaign_id]["conversions"] += metric.conversions or 0
            aggregated[campaign_id]["revenue"] += float(metric.revenue or 0)

        # Calculate derived metrics
        for campaign_id, data in aggregated.items():
            spend = data["spend"]
            clicks = data["clicks"]
            impressions = data["impressions"]
            revenue = data["revenue"]

            data["roas"] = revenue / spend if spend > 0 else 0
            data["ctr"] = (clicks / impressions * 100) if impressions > 0 else 0
            data["cpc"] = spend / clicks if clicks > 0 else 0
            data["conversion_rate"] = (data["conversions"] / clicks * 100) if clicks > 0 else 0

        return aggregated

    def _compare_periods(
        self,
        current_metrics: Dict[str, Dict[str, Any]],
        previous_metrics: Dict[str, Dict[str, Any]],
        run_id: str,
    ) -> List[Dict[str, Any]]:
        """Compare two periods and generate insights."""
        insights = []

        # Check all campaigns in current period
        for campaign_id, current in current_metrics.items():
            previous = previous_metrics.get(campaign_id, {})

            if not previous:
                # New campaign - opportunity
                insights.append({
                    "type": "opportunity",
                    "campaign_id": campaign_id,
                    "metric": "new_campaign",
                    "change_percent": None,
                    "description": "New campaign detected",
                    "severity": "medium",
                })
                continue

            # Compare key metrics
            metrics_to_check = ["roas", "ctr", "conversion_rate", "revenue"]

            for metric in metrics_to_check:
                current_val = current.get(metric, 0)
                previous_val = previous.get(metric, 0)

                if previous_val == 0:
                    continue

                change_percent = ((current_val - previous_val) / previous_val) * 100

                # Determine insight type and severity
                if change_percent < -20:
                    insights.append({
                        "type": "drop",
                        "campaign_id": campaign_id,
                        "metric": metric,
                        "change_percent": round(change_percent, 2),
                        "description": f"{metric.upper()} dropped {abs(change_percent):.1f}%",
                        "severity": "high" if change_percent < -30 else "medium",
                    })
                elif change_percent > 20:
                    insights.append({
                        "type": "opportunity",
                        "campaign_id": campaign_id,
                        "metric": metric,
                        "change_percent": round(change_percent, 2),
                        "description": f"{metric.upper()} increased {change_percent:.1f}%",
                        "severity": "high" if change_percent > 50 else "medium",
                    })

        return insights

