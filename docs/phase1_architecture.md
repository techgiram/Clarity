# Phase 1, Task 2: System Architecture & Folder Structure

## 1. 7-Agent Roles
1. Planner Agent: Breaks down query/mode into subtasks and search queries (Pydantic schema).
2. Web Research Agent: Fetches and deduplicates web sources/findings via Tavily.
3. Analysis Agent: Extracts key findings, trends, comparisons, opportunities, and risks.
4. Fact Verification Agent: Classifies claims as Verified, Partially Verified, Conflicting, or Unsupported.
5. Summarizer Agent: Produces concise executive summary while keeping caveats.
6. Report Generation Agent: Builds structured research report with citations and exports (MD, DOCX, PDF).
7. Quality Controller Agent: Audits completeness/citations and triggers bounded re-research if needed.

## 2. Orchestration & Shared State
- Orchestrated with LangGraph `StateGraph` using a typed shared state (`task`/`query`, `plan`, `research_data`, `analysis`, `verified_claims`, `summary`, `final_report`, `quality_feedback`, `retry_count`, etc.).
- Conditional edges route back to research only while `retry_count` is within the configured limit.

## 3. Security & Trust Boundaries
- Web search results and uploaded documents are treated as untrusted data, never system instructions.
- API keys stay in `.env` / environment variables and are never exposed in the frontend.

## 4. Target Folder Structure
`backend/` (`agents/`, `graph/`, `tools/`, `rag/`, `database/`, `schemas/`, `services/`, `core/`, `api/`, `utils/`), `frontend/`, `tests/`, `data/`, `reports/`, `scripts/`, `docs/`, `.github/workflows/`.
