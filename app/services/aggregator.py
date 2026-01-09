"""Aggregator - Combines all agent outputs into executive package."""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime


class Aggregator:
    """Aggregator for combining agent outputs."""

    def __init__(self, db: Session):
        self.db = db

    def aggregate(
        self,
        run_id: str,
        insights: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        creatives: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregate all agent outputs into a single executive package.
        
        Returns aggregated output dictionary.
        """
        # Count insights by type
        insight_counts = {}
        for insight in insights:
            insight_type = insight.get("type", "unknown")
            insight_counts[insight_type] = insight_counts.get(insight_type, 0) + 1

        # Count actions by type
        action_counts = {}
        for action in actions:
            action_type = action.get("type", "unknown")
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

        # Generate summary
        summary_parts = []
        if insight_counts.get("drop", 0) > 0:
            summary_parts.append(f"{insight_counts['drop']} performance drop(s) detected")
        if insight_counts.get("opportunity", 0) > 0:
            summary_parts.append(f"{insight_counts['opportunity']} opportunity(ies) identified")
        if action_counts.get("scale", 0) > 0:
            summary_parts.append(f"{action_counts['scale']} scaling recommendation(s)")
        if action_counts.get("test", 0) > 0:
            summary_parts.append(f"{action_counts['test']} test(s) recommended")

        summary = ". ".join(summary_parts) if summary_parts else "No significant changes detected."

        return {
            "run_id": str(run_id),
            "run_date": datetime.utcnow().isoformat(),
            "summary": summary,
            "insights": insights,
            "actions": actions,
            "creatives": creatives,
            "metrics": {
                "total_insights": len(insights),
                "total_actions": len(actions),
                "total_creatives": len(creatives),
                "insight_breakdown": insight_counts,
                "action_breakdown": action_counts,
            },
        }

