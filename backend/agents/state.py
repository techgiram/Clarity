from typing import TypedDict, List, Dict, Any, NotRequired


class ResearchState(TypedDict):
    """Shared LangGraph state across all 7 research agents."""
    task: str                                   # User research query/topic
    research_mode: NotRequired[str]             # Quick, Standard, Deep, Comparative, Technical, Academic
    session_id: NotRequired[str]                # Optional session identifier for persistence/UI
    plan: Dict[str, Any]                        # Planner agent structured plan
    research_data: List[str]                    # Raw/trimmed research findings
    rag_context: NotRequired[List[str]]         # Retrieved document chunks from RAG
    citations: NotRequired[List[Dict[str, Any]]]  # Structured SourceCitation metadata
    analysis: Dict[str, Any]                    # Analysis agent insights
    verified_claims: Dict[str, Any]             # Fact Verification output
    summary: str                                # Summarizer executive summary
    final_report: str                           # Final cited Markdown report
    quality_feedback: str                       # Quality Controller feedback
    retry_count: int                            # Bounded retry counter
