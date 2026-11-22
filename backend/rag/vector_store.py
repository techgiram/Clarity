import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.core.config import settings


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


class LocalVectorStore:
    """Persistent lightweight vector/lexical similarity store under data/vector_store."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: str = "research_docs"):
        self.persist_dir = Path(persist_dir or settings.vector_store_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.index_path = self.persist_dir / f"{collection_name}_index.json"
        self.records: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.index_path.exists():
            return []
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save(self) -> None:
        self.index_path.write_text(json.dumps(self.records, ensure_ascii=False, indent=2), encoding="utf-8")

    def ingest_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0

        existing_ids = {rec.get("id") for rec in self.records}
        added = 0

        for item in chunks:
            text = (item.get("text") or "").strip()
            meta = dict(item.get("metadata") or {})
            if not text:
                continue

            raw_id = f"{meta.get('source_path', '')}:{meta.get('chunk_index', '')}:{text[:120]}"
            doc_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:16]
            if doc_id in existing_ids:
                continue

            tokens = _tokenize(text)
            tf = dict(Counter(tokens))
            norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0

            self.records.append(
                {
                    "id": doc_id,
                    "text": text,
                    "metadata": meta,
                    "tf": tf,
                    "norm": norm,
                }
            )
            existing_ids.add(doc_id)
            added += 1

        if added > 0:
            self._save()
        return added

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not self.records or not query.strip():
            return []

        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        q_counts = Counter(q_tokens)
        q_norm = math.sqrt(sum(v * v for v in q_counts.values())) or 1.0

        scored: List[tuple[float, Dict[str, Any]]] = []
        for rec in self.records:
            tf = rec.get("tf") or {}
            doc_norm = float(rec.get("norm") or 1.0)
            dot = sum(q_freq * float(tf.get(tok, 0)) for tok, q_freq in q_counts.items())
            score = dot / (q_norm * doc_norm) if (q_norm * doc_norm) > 0 else 0.0
            if score > 0:
                scored.append((score, rec))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        results: List[Dict[str, Any]] = []
        for score, rec in scored[:top_k]:
            results.append(
                {
                    "id": rec["id"],
                    "text": rec["text"],
                    "metadata": rec.get("metadata", {}),
                    "score": round(score, 4),
                }
            )
        return results

    def count(self) -> int:
        return len(self.records)
