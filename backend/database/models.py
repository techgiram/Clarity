from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from backend.database.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    task = Column(Text, nullable=False)
    research_mode = Column(String(40), default="Standard", nullable=False)
    status = Column(String(30), default="completed", nullable=False)
    summary = Column(Text, default="", nullable=False)
    final_report = Column(Text, default="", nullable=False)
    plan_json = Column(Text, default="{}", nullable=False)
    analysis_json = Column(Text, default="{}", nullable=False)
    verified_claims_json = Column(Text, default="{}", nullable=False)
    citations_json = Column(Text, default="[]", nullable=False)
    quality_feedback = Column(Text, default="", nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class ResearchDocument(Base):
    __tablename__ = "research_documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_ext = Column(String(20), nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    uploaded_at = Column(DateTime, default=_utcnow, nullable=False)
