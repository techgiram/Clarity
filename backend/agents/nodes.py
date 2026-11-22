import time
from groq import BadRequestError, RateLimitError
from tavily import TavilyClient
from backend.core.config import settings
from backend.rag.vector_store import LocalVectorStore
from backend.services.llm_service import get_llm
from backend.schemas.research_schemas import (
    ResearchPlan,
    ResearchAnalysis,
    VerificationResult,
    QualityControlResult,
    SourceCitation,
)


# 1. Planner Agent
def planner_node(state: dict):
    print("\n--- [Planner Agent] Creating structured research plan ---")
    llm = get_llm()
    structured_llm = llm.with_structured_output(ResearchPlan)

    topic = state["task"]
    mode = state.get("research_mode", "Standard")
    prompt = f"""You are an expert research planner. Break down the following topic into logical subtasks and generate 3-4 specific web search queries.
    Research Mode: {mode}
    Topic: {topic}"""

    plan: ResearchPlan = structured_llm.invoke(prompt)
    print(f"Generated Objective: {plan.objective}")
    print(f"Search Queries: {plan.search_queries}")

    return {
        "plan": plan.model_dump(),
        "retry_count": state.get("retry_count", 0),
    }


# 2. Researcher Agent (Web + RAG)
def researcher_node(state: dict):
    print("\n--- [Researcher Agent] Fetching data from web and RAG store ---")
    tavily_api_key = settings.tavily_api_key
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables.")

    tavily = TavilyClient(api_key=tavily_api_key)

    plan = state.get("plan", {})
    queries = plan.get("search_queries") or [state["task"]]

    existing_citations = list(state.get("citations") or [])
    seen_sources = {c.get("url_or_path") for c in existing_citations if c.get("url_or_path")}
    all_findings = list(state.get("research_data") or [])
    rag_chunks_out = list(state.get("rag_context") or [])

    web_count = sum(1 for c in existing_citations if c.get("source_type") == "web")
    doc_count = sum(1 for c in existing_citations if c.get("source_type") == "rag")

    # 2a. Web search via Tavily
    for query in queries:
        print(f"Searching web for: {query}")
        response = tavily.search(query=query, max_results=2)
        results = response.get("results", [])
        for r in results:
            url = (r.get("url") or "").strip()
            title = (r.get("title") or "Untitled Source").strip()
            snippet = ((r.get("content") or "").strip())[:800]
            if not snippet:
                continue
            if url and url in seen_sources:
                continue

            web_count += 1
            source_id = f"S{web_count}"
            if url:
                seen_sources.add(url)

            citation = SourceCitation(
                source_id=source_id,
                title=title,
                url_or_path=url or "web-result",
                source_type="web",
                snippet=snippet,
            )
            existing_citations.append(citation.model_dump())
            all_findings.append(f"[{source_id}] ({title}) {snippet}")

    # 2b. Local RAG retrieval when documents are indexed
    store = LocalVectorStore()
    if store.count() > 0:
        rag_queries = [state["task"]] + list(queries[:2])
        for rq in rag_queries:
            hits = store.retrieve(rq, top_k=2)
            for hit in hits:
                meta = hit.get("metadata") or {}
                src_name = (meta.get("source_name") or "Uploaded Document").strip()
                chunk_idx = meta.get("chunk_index", 0)
                doc_key = f"rag://{src_name}#{chunk_idx}"
                snippet = ((hit.get("text") or "").strip())[:800]
                if not snippet or doc_key in seen_sources:
                    continue

                doc_count += 1
                doc_id = f"DOC{doc_count}"
                seen_sources.add(doc_key)

                citation = SourceCitation(
                    source_id=doc_id,
                    title=f"{src_name} (chunk {chunk_idx})",
                    url_or_path=doc_key,
                    source_type="rag",
                    snippet=snippet,
                )
                existing_citations.append(citation.model_dump())
                labeled = f"[{doc_id}] ({src_name}) {snippet}"
                rag_chunks_out.append(labeled)
                all_findings.append(labeled)

    return {
        "research_data": all_findings,
        "rag_context": rag_chunks_out,
        "citations": existing_citations,
    }


# 3. Analysis Agent
def analysis_node(state: dict):
    print("\n--- [Analysis Agent] Analyzing research findings ---")
    llm = get_llm()
    topic = state.get("task", "")
    findings = state.get("research_data", [])
    rag_ctx = state.get("rag_context", [])

    combined_text = "\n".join([str(x) for x in (findings + rag_ctx)])[:2600]
    prompt = f"""Analyze the following research findings for topic: '{topic}'.
Return a concise structured JSON object with keys:
- "key_findings": list of short key takeaway strings
- "themes": list of main theme strings
- "gaps": list of any open questions or limitations

Findings:
{combined_text}"""

    for attempt in range(3):
        try:
            raw = _invoke_with_rate_limit_retry(
                lambda: llm.invoke(prompt),
                label="analysis_agent",
                max_retries=3,
                base_wait=12.0,
            )
            content = raw.content if hasattr(raw, "content") else str(raw)
            parsed = None
            try:
                import json, re
                match = re.search(r"\{[\s\S]*\}", content)
                if match:
                    parsed = json.loads(match.group(0))
            except Exception:
                parsed = None

            if not isinstance(parsed, dict):
                lines = [ln.strip("-*? ").strip() for ln in content.splitlines() if ln.strip()]
                parsed = {
                    "key_findings": lines[:8] if lines else [combined_text[:300]],
                    "themes": [topic] if topic else [],
                    "gaps": [],
                }

            kf = parsed.get("key_findings") or []
            print(f"Extracted {len(kf)} key findings.")
            return {"analysis": parsed}
        except Exception as exc:
            print(f"Analysis retry {attempt + 1}/3 after error: {exc}")
            if attempt == 2:
                fallback_findings = [str(x)[:240] for x in findings[:6]] if findings else [combined_text[:300]]
                print(f"Extracted {len(fallback_findings)} key findings (fallback).")
                return {
                    "analysis": {
                        "key_findings": fallback_findings,
                        "themes": [topic] if topic else [],
                        "gaps": ["Rate limit or parsing fallback applied during analysis."],
                    }
                }
            time.sleep(3)

def verification_node(state: dict):
    print("\n--- [Fact Verification Agent] Verifying facts and claims ---")
    llm = get_llm()
    structured_llm = llm.with_structured_output(VerificationResult)

    topic = state.get("task", "")
    findings = "\n".join(state.get("research_data", []))[:1800]
    analysis = str(state.get("analysis", {}))[:1200]

    prompt = f"""Verify key claims for topic '{topic}' using only the provided research data and analysis.
Do not invent sources or URLs.

Research Data:
{findings}

Analysis:
{analysis}"""

    for attempt in range(3):
        try:
            res: VerificationResult = _invoke_with_rate_limit_retry(
                lambda: structured_llm.invoke(prompt),
                label="fact_verification",
                max_retries=3,
                base_wait=12.0,
            )
            claims_payload = res.model_dump() if hasattr(res, "model_dump") else dict(res or {})
            claims_list = claims_payload.get("claims") or []
            print(f"Verified {len(claims_list)} claims.")
            return {"verified_claims": {"claims": claims_list}}
        except Exception as exc:
            print(f"Schema validation issue on status field. Retrying with strict reminder... ({exc})")
            if attempt == 2:
                print("Fallback: returning empty verified claims list after schema retry.")
                return {"verified_claims": {"claims": []}}
            time.sleep(3)

    return {"verified_claims": {"claims": []}}

def summarizer_node(state: dict):
    print("\n--- [Summarizer Agent] Generating executive summary ---")
    llm = get_llm()
    analysis = state.get("analysis", {})
    topic = state["task"]

    prompt = f"""Write a concise, professional executive summary and highlight the top insights for the research topic: '{topic}'.
    Key Findings: {analysis.get('key_findings')}
    Trends: {analysis.get('trends')}
    """

    response = llm.invoke(prompt)
    summary_content = response.content if hasattr(response, "content") else str(response)
    return {"summary": summary_content}


# 6. Writer Agent

def _invoke_with_rate_limit_retry(fn, label: str = "llm_call", max_retries: int = 3, base_wait: float = 12.0):
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_s = base_wait * (attempt + 1)
                print(f"TPM rate limit in {label}. Waiting {wait_s:.0f}s before retry ({attempt + 1}/{max_retries - 1})...")
                time.sleep(wait_s)
            else:
                raise


def writer_node(state: dict):
    print("\n--- [Writer Agent] Drafting final research report ---")
    llm = get_llm()

    topic = state["task"]
    plan = state.get("plan", {})
    findings = "\n".join(state.get("research_data", []))[:1800]
    citations = str(state.get("citations", []))[:1200]
    analysis = state.get("analysis", {})
    summary = (state.get("summary", "") or "")[:1000]

    prompt = f"""Write a concise, well-structured markdown research report on: '{topic}'.
Use only the provided data and citations; do NOT invent URLs or citations.

Executive Summary: {summary}
Objective: {plan.get('objective')}
Key Findings: {analysis.get('key_findings')}
Trends: {analysis.get('trends')}
Detailed Data: {findings}
Sources Metadata: {citations}

Include headings, key takeaways, a Sources section, and a brief conclusion."""

    for attempt in range(3):
        try:
            response = llm.invoke(prompt)
            report_content = response.content if hasattr(response, "content") else str(response)
            return {"final_report": report_content}
        except RateLimitError:
            if attempt < 2:
                wait_s = 12 * (attempt + 1)
                print(f"TPM rate limit in writer. Waiting {wait_s}s before retry ({attempt + 1}/2)...")
                time.sleep(wait_s)
            else:
                raise


# 7. Quality Controller Agent
def quality_controller_node(state: dict):
    print("\n--- [Quality Controller Agent] Evaluating report quality ---")
    llm = get_llm()
    structured_llm = llm.with_structured_output(QualityControlResult)

    report = state.get("final_report", "")
    topic = state["task"]

    prompt = f"""Evaluate if this research report adequately answers the user's topic: '{topic}'.
Report: {report[:2000]}
Determine if it is sufficient or if re-research is needed."""

    for attempt in range(3):
        try:
            qc: QualityControlResult = structured_llm.invoke(prompt)
            print(f"Quality Check - Is Sufficient: {qc.is_sufficient}")

            retry_count = state.get("retry_count", 0)
            if not qc.is_sufficient or qc.needs_re_research:
                retry_count += 1

            return {
                "quality_feedback": qc.feedback,
                "retry_count": retry_count,
            }
        except RateLimitError:
            if attempt < 2:
                wait_s = 12 * (attempt + 1)
                print(f"TPM rate limit in quality controller. Waiting {wait_s}s before retry ({attempt + 1}/2)...")
                time.sleep(wait_s)
            else:
                raise
