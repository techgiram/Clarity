import traceback



import json



import uuid



from contextlib import asynccontextmanager



from pathlib import Path



from typing import Any, Dict, List, Literal, Optional







from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile



from fastapi.responses import Response



from pydantic import BaseModel, Field



from sqlalchemy.orm import Session







from backend.agents.graph import create_research_graph



from backend.core.config import settings



from backend.database.db import get_db, init_db



from backend.database.repository import (



    get_research_run_by_session,



    list_research_runs,



    list_uploaded_documents,



    record_uploaded_document,



    save_research_run,



)



from backend.exports.report_exporter import (



    export_docx_bytes,



    export_markdown_bytes,



    export_pdf_bytes,



)



from backend.rag.document_loader import load_and_chunk_document



from backend.rag.vector_store import LocalVectorStore



from backend.schemas.research_schemas import ResearchMode











@asynccontextmanager



async def lifespan(app: FastAPI):



    init_db()



    Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)



    Path(settings.vector_store_dir).mkdir(parents=True, exist_ok=True)



    yield











app = FastAPI(



    title="Multi-Agent AI Research & Intelligence API",



    version="1.0.0",



    lifespan=lifespan,



)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)












class ResearchRunRequest(BaseModel):



    task: str = Field(..., min_length=3, description="Research topic or question.")



    research_mode: ResearchMode = Field(default="Standard", description="Research depth/style mode.")



    session_id: Optional[str] = Field(default=None, description="Optional custom session identifier.")











class ResearchRunResponse(BaseModel):



    session_id: str



    task: str



    research_mode: str



    status: str



    summary: str



    final_report: str



    plan: Dict[str, Any]



    analysis: Dict[str, Any]



    verified_claims: Dict[str, Any]



    citations: List[Dict[str, Any]]



    quality_feedback: str



    retry_count: int











def _safe_json_loads(raw: str, fallback: Any) -> Any:



    try:



        return json.loads(raw) if raw else fallback



    except Exception:



        return fallback











@app.get("/health")



def health_check(db: Session = Depends(get_db)):



    key_status = settings.validate_keys()



    return {



        "status": "ok",



        "app_name": settings.app_name,



        "default_llm_model": settings.default_llm_model,



        "keys_configured": key_status,



        "database": "connected",



    }











@app.post("/documents/upload")



async def upload_document(



    file: UploadFile = File(...),



    db: Session = Depends(get_db),



):



    if not file.filename:



        raise HTTPException(status_code=400, detail="Filename is required.")







    safe_name = Path(file.filename).name



    ext = Path(safe_name).suffix.lower()



    if ext not in {".pdf", ".docx", ".txt", ".csv"}:



        raise HTTPException(



            status_code=400,



            detail=f"Unsupported file type '{ext}'. Allowed: .pdf, .docx, .txt, .csv",



        )







    upload_dir = Path("data/uploads")



    upload_dir.mkdir(parents=True, exist_ok=True)



    dest_path = upload_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"







    content = await file.read()



    dest_path.write_bytes(content)







    try:



        chunks = load_and_chunk_document(str(dest_path))



        store = LocalVectorStore()



        added_chunks = store.ingest_chunks(chunks)



    except Exception as exc:



        raise HTTPException(status_code=422, detail=f"Failed to process document: {exc}") from exc







    doc_record = record_uploaded_document(



        db=db,



        file_name=safe_name,



        file_path=str(dest_path.resolve()),



        file_ext=ext,



        chunk_count=len(chunks),



    )







    return {



        "id": doc_record.id,



        "file_name": doc_record.file_name,



        "file_ext": doc_record.file_ext,



        "chunk_count": doc_record.chunk_count,



        "newly_indexed_chunks": added_chunks,



        "total_store_chunks": store.count(),



    }











@app.get("/documents")



def get_documents(limit: int = 50, db: Session = Depends(get_db)):



    docs = list_uploaded_documents(db=db, limit=limit)



    return [



        {



            "id": d.id,



            "file_name": d.file_name,



            "file_ext": d.file_ext,



            "chunk_count": d.chunk_count,



            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,



        }



        for d in docs



    ]











@app.post("/research/run", response_model=ResearchRunResponse)



def run_research(payload: ResearchRunRequest, db: Session = Depends(get_db)):



    session_id = (payload.session_id or "").strip() or str(uuid.uuid4())



    graph = create_research_graph()







    initial_state: Dict[str, Any] = {



        "task": payload.task,



        "research_mode": payload.research_mode,



        "session_id": session_id,



        "plan": {},



        "research_data": [],



        "rag_context": [],



        "citations": [],



        "analysis": {},



        "verified_claims": {},



        "summary": "",



        "final_report": "",



        "quality_feedback": "",



        "retry_count": 0,



    }







    try:



        result_state = graph.invoke(initial_state)



    except Exception as exc:



        print("\n=== RESEARCH WORKFLOW 500 ROOT CAUSE TRACEBACK ===")



        traceback.print_exc()



        print("==============================================\n")



        error_state = dict(initial_state)



        error_state["quality_feedback"] = f"{type(exc).__name__}: {exc}"



        save_research_run(db=db, state=error_state, status="failed")



        raise HTTPException(status_code=500, detail=f"Research workflow failed ({type(exc).__name__}): {exc}") from exc







    result_state["session_id"] = session_id



    result_state["task"] = payload.task



    result_state["research_mode"] = payload.research_mode







    saved_run = save_research_run(db=db, state=result_state, status="completed")







    return ResearchRunResponse(



        session_id=saved_run.session_id,



        task=saved_run.task,



        research_mode=saved_run.research_mode,



        status=saved_run.status,



        summary=saved_run.summary,



        final_report=saved_run.final_report,



        plan=_safe_json_loads(saved_run.plan_json, {}),



        analysis=_safe_json_loads(saved_run.analysis_json, {}),



        verified_claims=_safe_json_loads(saved_run.verified_claims_json, {}),



        citations=_safe_json_loads(saved_run.citations_json, []),



        quality_feedback=saved_run.quality_feedback,



        retry_count=saved_run.retry_count,



    )











@app.get("/research/runs")



def get_runs(limit: int = 30, db: Session = Depends(get_db)):



    runs = list_research_runs(db=db, limit=limit)



    return [



        {



            "session_id": r.session_id,



            "task": r.task,



            "research_mode": r.research_mode,



            "status": r.status,



            "retry_count": r.retry_count,



            "created_at": r.created_at.isoformat() if r.created_at else None,



        }



        for r in runs



    ]











@app.get("/research/runs/{session_id}", response_model=ResearchRunResponse)



def get_run_detail(session_id: str, db: Session = Depends(get_db)):



    run = get_research_run_by_session(db=db, session_id=session_id)



    if not run:



        raise HTTPException(status_code=404, detail="Research run not found.")







    return ResearchRunResponse(



        session_id=run.session_id,



        task=run.task,



        research_mode=run.research_mode,



        status=run.status,



        summary=run.summary,



        final_report=run.final_report,



        plan=_safe_json_loads(run.plan_json, {}),



        analysis=_safe_json_loads(run.analysis_json, {}),



        verified_claims=_safe_json_loads(run.verified_claims_json, {}),



        citations=_safe_json_loads(run.citations_json, []),



        quality_feedback=run.quality_feedback,



        retry_count=run.retry_count,



    )











@app.get("/research/runs/{session_id}/export")



def export_run_report(



    session_id: str,



    fmt: Literal["md", "docx", "pdf"] = Query(default="md"),



    db: Session = Depends(get_db),



):



    run = get_research_run_by_session(db=db, session_id=session_id)



    if not run:



        raise HTTPException(status_code=404, detail="Research run not found.")







    title = run.task or "Research Report"



    safe_slug = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in title[:40]).strip("_") or "report"







    if fmt == "md":



        data = export_markdown_bytes(title=title, report_markdown=run.final_report, summary=run.summary)



        return Response(



            content=data,



            media_type="text/markdown; charset=utf-8",



            headers={"Content-Disposition": f'attachment; filename="{safe_slug}.md"'},



        )







    if fmt == "docx":



        data = export_docx_bytes(title=title, report_markdown=run.final_report, summary=run.summary)



        return Response(



            content=data,



            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",



            headers={"Content-Disposition": f'attachment; filename="{safe_slug}.docx"'},



        )







    data = export_pdf_bytes(title=title, report_markdown=run.final_report, summary=run.summary)



    return Response(



        content=data,



        media_type="application/pdf",



        headers={"Content-Disposition": f'attachment; filename="{safe_slug}.pdf"'},



    )

# --- Serve Built React Frontend (Clarity Single-Service) ---
from pathlib import Path as _Path
from fastapi.responses import FileResponse as _FileResponse
from fastapi.staticfiles import StaticFiles as _StaticFiles

_CLARITY_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _CLARITY_DIST.exists():
    _assets = _CLARITY_DIST / "assets"
    if _assets.exists():
        app.mount("/assets", _StaticFiles(directory=str(_assets)), name="clarity-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _serve_clarity_spa(full_path: str):
        candidate = (_CLARITY_DIST / full_path).resolve()
        dist_resolved = _CLARITY_DIST.resolve()
        if full_path and str(candidate).startswith(str(dist_resolved)) and candidate.is_file():
            return _FileResponse(str(candidate))
        return _FileResponse(str(_CLARITY_DIST / "index.html"))
