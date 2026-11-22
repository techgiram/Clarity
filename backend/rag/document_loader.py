from pathlib import Path
from typing import Any, Dict, List
import fitz  # PyMuPDF
import docx
import pandas as pd


def _extract_raw_text(file_path: Path) -> str:
    ext = file_path.suffix.lower()

    if ext == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".csv":
        df = pd.read_csv(file_path)
        return df.to_string(index=False)

    if ext == ".pdf":
        pages: List[str] = []
        with fitz.open(file_path) as doc:
            for idx, page in enumerate(doc, start=1):
                txt = (page.get_text("text") or "").strip()
                if txt:
                    pages.append(f"[Page {idx}] {txt}")
        return "\n\n".join(pages)

    if ext == ".docx":
        doc = docx.Document(str(file_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
        return "\n\n".join(paragraphs)

    raise ValueError(f"Unsupported file format: {ext}. Supported formats: .pdf, .docx, .txt, .csv")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    chunks: List[str] = []
    start = 0
    step = chunk_size - overlap
    while start < len(cleaned):
        piece = cleaned[start : start + chunk_size].strip()
        if piece:
            chunks.append(piece)
        start += step
    return chunks


def load_and_chunk_document(
    path_str: str,
    chunk_size: int = 800,
    overlap: int = 120,
) -> List[Dict[str, Any]]:
    file_path = Path(path_str)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Document not found: {file_path}")

    raw_text = _extract_raw_text(file_path)
    pieces = chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)

    records: List[Dict[str, Any]] = []
    for i, chunk in enumerate(pieces):
        records.append(
            {
                "text": chunk,
                "metadata": {
                    "source_name": file_path.name,
                    "source_path": str(file_path.resolve()),
                    "chunk_index": i,
                    "source_type": "rag",
                },
            }
        )
    return records
