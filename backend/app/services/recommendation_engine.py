from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.standard import StandardModel

_token_re = re.compile(r"\w+")


@dataclass
class RetrievalHit:
    standard_id: int
    score: float


class StandardsRecommendationEngine:
    def __init__(self, db: Session):
        self.db = db
        self._embedder: SentenceTransformer | None = None
        self._reranker: CrossEncoder | None = None
        self._bm25: BM25Okapi | None = None
        self._bm25_ids: list[int] = []
        self._faiss_index: faiss.IndexFlatIP | None = None
        self._faiss_ids: list[int] = []
        self._corpus: dict[int, str] = {}
        self._rows: dict[int, StandardModel] = {}
        self._built = False

    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            self._embedder = SentenceTransformer(settings.embedding_model)
        return self._embedder

    @property
    def reranker(self) -> CrossEncoder:
        if self._reranker is None:
            self._reranker = CrossEncoder(settings.reranker_model)
        return self._reranker

    def _tokenize(self, text: str) -> list[str]:
        return _token_re.findall(text.lower())

    def build_indexes(self, force: bool = False) -> None:
        if self._built and not force:
            return

        faiss_path = Path(settings.faiss_index_path)
        bm25_path = Path(settings.bm25_index_path)
        faiss_path.parent.mkdir(parents=True, exist_ok=True)

        rows = self.db.query(StandardModel).all()
        if not rows:
            self._built = True
            return

        for r in rows:
            self._rows[r.id] = r
            self._corpus[r.id] = r.search_text or r.title.lower()

        ids = [r.id for r in rows]
        tokenized = [self._tokenize(self._corpus[i]) for i in ids]

        if not force and bm25_path.exists() and faiss_path.exists():
            with bm25_path.open("rb") as f:
                payload = pickle.load(f)
                self._bm25 = payload["bm25"]
                self._bm25_ids = payload["ids"]
            self._faiss_index = faiss.read_index(str(faiss_path))
            with (faiss_path.parent / "faiss_ids.pkl").open("rb") as f:
                self._faiss_ids = pickle.load(f)
            self._built = True
            return

        self._bm25 = BM25Okapi(tokenized)
        self._bm25_ids = ids

        texts = [self._corpus[i] for i in ids]
        embeddings = self.embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        embeddings = np.asarray(embeddings, dtype=np.float32)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        self._faiss_index = index
        self._faiss_ids = ids

        faiss.write_index(index, str(faiss_path))
        with (faiss_path.parent / "faiss_ids.pkl").open("wb") as f:
            pickle.dump(self._faiss_ids, f)
        with bm25_path.open("wb") as f:
            pickle.dump({"bm25": self._bm25, "ids": self._bm25_ids}, f)

        self._built = True

    def _bm25_search(self, query: str, top_k: int = 20) -> list[RetrievalHit]:
        if not self._bm25:
            return []
        tokens = self._tokenize(query)
        scores = self._bm25.get_scores(tokens)
        ranked = np.argsort(scores)[::-1][:top_k]
        return [RetrievalHit(self._bm25_ids[i], float(scores[i])) for i in ranked if scores[i] > 0]

    def _vector_search(self, query: str, top_k: int = 20) -> list[RetrievalHit]:
        if not self._faiss_index:
            return []
        q = self.embedder.encode([query], normalize_embeddings=True, show_progress_bar=False)
        q = np.asarray(q, dtype=np.float32)
        k = min(top_k, len(self._faiss_ids))
        scores, idx = self._faiss_index.search(q, k)
        hits = []
        for j, i in enumerate(idx[0]):
            if i < 0:
                continue
            hits.append(RetrievalHit(self._faiss_ids[i], float(scores[0][j])))
        return hits

    @staticmethod
    def merge_results(*result_lists: list[RetrievalHit], top_k: int = 30) -> list[int]:
        scores: dict[int, float] = {}
        for results in result_lists:
            if not results:
                continue
            max_s = max(r.score for r in results) or 1.0
            for r in results:
                norm = r.score / max_s
                scores[r.standard_id] = scores.get(r.standard_id, 0.0) + norm
        ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [sid for sid, _ in ordered[:top_k]]

    def recommend(self, query: str, top_k: int = 5) -> list[tuple[StandardModel, float]]:
        self.build_indexes()
        if not self._rows:
            return []

        bm25_hits = self._bm25_search(query, top_k=20)
        vector_hits = self._vector_search(query, top_k=20)
        candidate_ids = self.merge_results(bm25_hits, vector_hits, top_k=30)

        if not candidate_ids:
            # fallback: SQL LIKE
            q = f"%{query[:80]}%"
            fallback = (
                self.db.query(StandardModel)
                .filter(StandardModel.search_text.like(q))
                .limit(top_k)
                .all()
            )
            return [(r, 0.5) for r in fallback]

        candidates = [self._rows[cid] for cid in candidate_ids if cid in self._rows]
        pairs = [(query, f"{c.is_number} {c.title}. {c.abstract}") for c in candidates]
        rerank_scores = self.reranker.predict(pairs)
        ranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)

        # Normalize scores to 0-1 via sigmoid-ish scaling
        out = []
        for row, raw in ranked[:top_k]:
            score = float(1 / (1 + np.exp(-raw)))
            out.append((row, score))
        return out


_engine_cache: StandardsRecommendationEngine | None = None
_engine_db_id: int | None = None


def get_engine(db: Session) -> StandardsRecommendationEngine:
    global _engine_cache, _engine_db_id
    db_id = id(db.get_bind())
    if _engine_cache is None or _engine_db_id != db_id:
        _engine_cache = StandardsRecommendationEngine(db)
        _engine_db_id = db_id
    return _engine_cache


def rebuild_indexes(db: Session) -> None:
    engine = get_engine(db)
    engine.build_indexes(force=True)
