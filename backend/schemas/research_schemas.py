from typing import List, Literal, Optional
from pydantic import BaseModel, Field

ResearchMode = Literal["Quick", "Standard", "Deep", "Comparative", "Technical", "Academic"]


class SourceCitation(BaseModel):
    source_id: str = Field(description="Short citation identifier such as S1, S2, or DOC1.")
    title: str = Field(description="Title of the web page or uploaded document.")
    url_or_path: str = Field(description="Source URL or document file reference.")
    source_type: Literal["web", "rag"] = Field(default="web", description="Origin of the source.")
    snippet: str = Field(default="", description="Relevant excerpt supporting claims.")


# 1. Planner Agent Schema
class ResearchPlan(BaseModel):
    objective: str = Field(description="The core objective of the research.")
    subtasks: List[str] = Field(description="Logical subtasks to break down the topic.")
    search_queries: List[str] = Field(description="3 to 4 specific search queries for web search.")


# 2. Fact Verification Agent Schema
class VerifiedClaim(BaseModel):
    claim: str = Field(description="The factual statement extracted from findings.")
    status: Literal["Verified", "Partially Verified", "Conflicting", "Unsupported"] = Field(
        description="Verification status based on evidence."
    )
    evidence: str = Field(description="Supporting or conflicting evidence from sources.")
    citation_ids: List[str] = Field(default_factory=list, description="Matching SourceCitation IDs.")


class VerificationResult(BaseModel):
    claims: List[VerifiedClaim] = Field(description="List of evaluated claims.")


# 3. Analysis Agent Schema
class ResearchAnalysis(BaseModel):
    key_findings: List[str] = Field(description="Key findings and insights extracted from research data.")
    trends: List[str] = Field(description="Important trends or patterns identified.")
    limitations: List[str] = Field(description="Limitations, gaps, or risks identified in the research.")


# 4. Quality Controller Agent Schema
class QualityControlResult(BaseModel):
    is_sufficient: bool = Field(description="True if the research is complete and answers the objective, False otherwise.")
    feedback: str = Field(description="Feedback on what is missing or needs improvement if insufficient.")
    needs_re_research: bool = Field(description="True if we need to send back to researcher/planner.")
