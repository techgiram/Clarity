from langgraph.graph import StateGraph, END
from backend.core.config import settings
from backend.agents.state import ResearchState
from backend.agents.nodes import (
    planner_node,
    researcher_node,
    analysis_node,
    verification_node,
    summarizer_node,
    writer_node,
    quality_controller_node,
)


def should_continue(state: ResearchState):
    retry_count = state.get("retry_count", 0)
    max_retries = settings.max_research_retries

    if 0 < retry_count <= max_retries:
        print(f"Quality Check Failed! Re-running research (Attempt {retry_count}/{max_retries})...")
        return "re_research"

    return "end"


def create_research_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("summarizer", summarizer_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("quality_controller", quality_controller_node)

    workflow.set_entry_point("planner")

    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "analysis")
    workflow.add_edge("analysis", "verification")
    workflow.add_edge("verification", "summarizer")
    workflow.add_edge("summarizer", "writer")
    workflow.add_edge("writer", "quality_controller")

    workflow.add_conditional_edges(
        "quality_controller",
        should_continue,
        {
            "end": END,
            "re_research": "planner",
        },
    )

    return workflow.compile()
