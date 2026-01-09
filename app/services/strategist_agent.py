"""Strategist Agent - Makes strategic decisions based on insights."""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.agent import Action
from uuid import uuid4


class StrategistAgent:
    """Strategist Agent for making strategic decisions."""

    def __init__(self, db: Session):
        self.db = db

    def decide(
        self,
        run_id: str,
        insights: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Make strategic decisions based on insights.
        
        Returns list of action dictionaries.
        """
        actions = []

        # Group insights by campaign
        campaign_insights = {}
        for insight in insights:
            campaign_id = insight.get("campaign_id")
            if campaign_id not in campaign_insights:
                campaign_insights[campaign_id] = []
            campaign_insights[campaign_id].append(insight)

        # Generate actions for each campaign
        for campaign_id, campaign_insight_list in campaign_insights.items():
            # Analyze insights for this campaign
            has_drop = any(i["type"] == "drop" for i in campaign_insight_list)
            has_opportunity = any(i["type"] == "opportunity" for i in campaign_insight_list)
            high_severity_drop = any(
                i["type"] == "drop" and i.get("severity") == "high"
                for i in campaign_insight_list
            )

            # Decision logic
            if high_severity_drop:
                # Pause or fix underperformers
                actions.append({
                    "type": "fix",
                    "campaign_id": campaign_id,
                    "description": "High severity performance drop detected - requires investigation",
                    "priority": "high",
                })
            elif has_opportunity and not has_drop:
                # Scale winners
                actions.append({
                    "type": "scale",
                    "campaign_id": campaign_id,
                    "description": "Strong performance - recommend scaling budget",
                    "priority": "high",
                })
            elif has_opportunity:
                # Test new approaches
                actions.append({
                    "type": "test",
                    "campaign_id": campaign_id,
                    "description": "Mixed signals - recommend testing new creative variants",
                    "priority": "medium",
                })

        # Save actions to database
        for action_data in actions:
            action = Action(
                id=uuid4(),
                agent_run_id=run_id,
                action_type=action_data["type"],
                campaign_id=action_data.get("campaign_id"),
                description=action_data.get("description"),
                priority=action_data.get("priority", "medium"),
                status="pending",
            )
            self.db.add(action)

        self.db.commit()

        return actions

