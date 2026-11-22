import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import ResearchDocument, ResearchRun


def save_research_run(db: Session, state: Dict[str, Any], status: str = "completed") -> ResearchRun:
    session_id = (state.get("session_id") or "").strip() or str(uuid.uuid4())
    existing = db.query(ResearchRun).filter(ResearchRun.session_id == session_id).first()

    plan_str = json.dumps(state.get("plan") or {}, ensure_ascii=False)
    analysis_str = json.dumps(state.get("analysis") or {}, ensure_ascii=False)
    claims_str = json.dumps(state.get("verified_claims") or {}, ensure_ascii=False)
    citations_str = json.dumps(state.get("citations") or [], ensure_ascii=False)

    if existing:
        existing.task = state.get("task", existing.task)
        existing.research_mode = state.get("research_mode") or existing.research_mode
        existing.status = status
        existing.summary = state.get("summary") or ""
        existing.final_report = state.get("final_report") or ""
        existing.plan_json = plan_str
        existing.analysis_json = analysis_str
        existing.verified_claims_json = claims_str
        existing.citations_json = citations_str
        existing.quality_feedback = state.get("quality_feedback") or ""
        existing.retry_count = int(state.get("retry_count") or 0)
        db.commit()
        db.refresh(existing)
        return existing

    run = ResearchRun(
        session_id=session_id,
        task=state.get("task", ""),
        research_mode=state.get("research_mode") or "Standard",
        status=status,
        summary=state.get("summary") or "",
        final_report=state.get("final_report") or "",
        plan_json=plan_str,
        analysis_json=analysis_str,
        verified_claims_json=claims_str,
        citations_json=citations_str,
        quality_feedback=state.get("quality_feedback") or "",
        retry_count=int(state.get("retry_count") or 0),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_research_runs(db: Session, limit: int = 50) -> List[ResearchRun]:
    return db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(limit).all()


def get_research_run_by_session(db: Session, session_id: str) -> Optional[ResearchRun]:
    return db.query(ResearchRun).filter(ResearchRun.session_id == session_id).first()


def record_uploaded_document(
    db: Session,
    file_name: str,
    file_path: str,
    file_ext: str,
    chunk_count: int,
) -> ResearchDocument:
    doc = ResearchDocument(
        file_name=file_name,
        file_path=file_path,
        file_ext=file_ext.lower(),
        chunk_count=chunk_count,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_uploaded_documents(db: Session, limit: int = 100) -> List[ResearchDocument]:
    return db.query(ResearchDocument).order_by(ResearchDocument.uploaded_at.desc()).limit(limit).all()
