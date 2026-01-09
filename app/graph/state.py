"""State definition for LangGraph state machine."""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class AgentState(TypedDict):
    """State passed between LangGraph nodes."""

    # Run metadata
    run_id: str
    run_type: str
    started_at: datetime

    # Input parameters
    days_back: int
    comparison_days: int

    # Data collection
    metrics_data: Optional[Dict[str, Any]]

    # Agent outputs
    insights: Optional[List[Dict[str, Any]]]
    actions: Optional[List[Dict[str, Any]]]
    creatives: Optional[List[Dict[str, Any]]]

    # Final output
    aggregated_output: Optional[Dict[str, Any]]

    # Error handling
    error: Optional[str]
    status: str  # 'running', 'completed', 'failed'



