"""LangGraph nodes for the state machine."""

from typing import Dict, Any
from datetime import datetime
from app.graph.state import AgentState
from app.services.analytics_agent import AnalyticsAgent
from app.services.strategist_agent import StrategistAgent
from app.services.content_agent import ContentAgent
from app.services.aggregator import Aggregator
from sqlalchemy.orm import Session


def collect_data_node(state: AgentState, db: Session) -> Dict[str, Any]:
    """
    Node 1: Collect data from database.
    This is a placeholder - in the full implementation, this would query the DB.
    """
    return {
        "metrics_data": {
            "message": "Data collection placeholder - will query DB in full implementation",
            "days_back": state["days_back"],
        }
    }


def analyze_node(state: AgentState, db: Session) -> Dict[str, Any]:
    """
    Node 2: Analytics Agent - Analyze performance.
    """
    analytics_agent = AnalyticsAgent(db)
    # Note: This is a simplified version - in full implementation, we'd use async
    insights = analytics_agent.analyze(
        run_id=state["run_id"],
        days_back=state["days_back"],
        comparison_days=state["comparison_days"],
    )
    return {"insights": insights}


def decide_node(state: AgentState, db: Session) -> Dict[str, Any]:
    """
    Node 3: Strategist Agent - Make decisions.
    """
    strategist_agent = StrategistAgent(db)
    actions = strategist_agent.decide(
        run_id=state["run_id"],
        insights=state.get("insights", []),
    )
    return {"actions": actions}


def create_node(state: AgentState, db: Session) -> Dict[str, Any]:
    """
    Node 4: Content Agent - Generate creatives.
    """
    content_agent = ContentAgent(db)
    creatives = content_agent.create(
        run_id=state["run_id"],
        actions=state.get("actions", []),
    )
    return {"creatives": creatives}


def aggregate_node(state: AgentState, db: Session) -> Dict[str, Any]:
    """
    Node 5: Aggregator - Combine all outputs.
    """
    aggregator = Aggregator(db)
    aggregated_output = aggregator.aggregate(
        run_id=state["run_id"],
        insights=state.get("insights", []),
        actions=state.get("actions", []),
        creatives=state.get("creatives", []),
    )
    return {
        "aggregated_output": aggregated_output,
        "status": "completed",
    }


def error_node(state: AgentState, error: Exception) -> Dict[str, Any]:
    """
    Error handling node.
    """
    return {
        "error": str(error),
        "status": "failed",
    }



