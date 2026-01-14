"""LangGraph state machine definition."""

from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import (
    collect_data_node,
    analyze_node,
    decide_node,
    create_node,
    aggregate_node,
    error_node,
)
from sqlalchemy.orm import Session


def create_agent_graph(db: Session) -> StateGraph:
    """
    Create the LangGraph state machine for agent execution.
    
    Flow:
    CollectData → Analyze → Decide → Create → Aggregate → Done
    """
    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("collect_data", lambda state: collect_data_node(state, db))
    workflow.add_node("analyze", lambda state: analyze_node(state, db))
    workflow.add_node("decide", lambda state: decide_node(state, db))
    workflow.add_node("create", lambda state: create_node(state, db))
    workflow.add_node("aggregate", lambda state: aggregate_node(state, db))

    # Define edges
    workflow.set_entry_point("collect_data")
    workflow.add_edge("collect_data", "analyze")
    workflow.add_edge("analyze", "decide")
    workflow.add_edge("decide", "create")
    workflow.add_edge("create", "aggregate")
    workflow.add_edge("aggregate", END)

    # Compile graph
    app = workflow.compile()

    return app


# Note: In the full implementation with LangGraph, we would use:
# from langgraph.graph import StateGraph, END
# 
# However, for MVP, we're using a simplified approach where the
# agent_service orchestrates the agents directly. This can be
# migrated to full LangGraph later when we add:
# - Conditional routing
# - Retry logic
# - Parallel execution
# - Human-in-the-loop nodes





