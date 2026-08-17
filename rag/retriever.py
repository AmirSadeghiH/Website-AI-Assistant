import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import faiss
import numpy as np

from rag.embeddings import Embedder


class EmbeddingDimensionMismatchError(RuntimeError):
    """The query embedding dimension does not match the corpus index.

    Usually caused by changing EMBEDDING_MODEL (or the panel embedding model)
    after the knowledge documents were processed.
    """


class Retriever:
    """FAISS retriever with bounded search and per-process query embedding cache.

    A fresh installation with no processed documents is a valid state: all
    three corpus artifacts missing means an empty knowledge base and
    ``retrieve`` returns ``[]``. Partial artifacts are treated as corruption.
    """

    def __init__(
        self,
        chunks_path: str | None = None,
        metadata_path: str | None = None,
        embeddings_path: str | None = None,
        device: Optional[str] = None,
        normalize: bool = True,
        embedder: Optional[Embedder] = None,
    ):
        data_dir = Path(__file__).resolve().parent.parent / "Data"
        chunks_path = chunks_path or str(data_dir / "chunks.json")
        metadata_path = metadata_path or str(data_dir / "metadata.json")
        embeddings_path = embeddings_path or str(data_dir / "embeddings.npy")

        chunk_file = Path(chunks_path)
        metadata_file = Path(metadata_path)
        embeddings_file = Path(embeddings_path)
        existing = [
            path.exists() for path in (chunk_file, metadata_file, embeddings_file)
        ]

        if not any(existing):
            # Empty corpus — a fresh install with no documents processed yet.
            self.chunks: List[str] = []
            self.metadata: List[Dict] = []
            self.embeddings: np.ndarray = np.empty((0, 0), dtype="float32")
            self.index = None
            self.embedder = embedder or Embedder(device=device)
            return

        if not all(existing):
            raise RuntimeError(
                "RAG corpus is inconsistent. chunks.json, metadata.json and "
                "embeddings.npy must all exist together; delete the remaining "
                "files or re-process the documents."
            )

        try:
            with open(chunks_path, "r", encoding="utf-8") as file:
                self.chunks: List[str] = json.load(file)
            with open(metadata_path, "r", encoding="utf-8") as file:
                self.metadata: List[Dict] = json.load(file)
            self.embeddings: np.ndarray = np.load(embeddings_path).astype("float32")
        except (FileNotFoundError, ValueError) as exc:
            raise RuntimeError(
                "RAG corpus is unreadable. Re-process the knowledge documents."
            ) from exc

        if (
            not self.chunks
            or len(self.chunks) != len(self.metadata)
            or len(self.chunks) != self.embeddings.shape[0]
            or self.embeddings.ndim != 2
        ):
            raise RuntimeError("RAG corpus artifacts are inconsistent.")

        if normalize:
            faiss.normalize_L2(self.embeddings)

        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)
        self.embedder = embedder or Embedder(device=device)
        self._retrieve_cache = {}

    @lru_cache(maxsize=512)
    def _embed_query_cached(self, query: str) -> np.ndarray:
        return self.embedder.embed_query_api(query).astype("float32")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        abs_min_score: float = 0.10,
        rel_score_drop: float = 0.4,
        fallback_top_k: int = 5,
    ) -> List[Dict]:
        if not self.chunks or self.index is None:
            return []

        query = str(query).strip()[:2000]
        query_emb = self._embed_query_cached(query).copy()
        if query_emb.shape[0] != self.index.d:
            raise EmbeddingDimensionMismatchError(
                f"Query embedding is {query_emb.shape[0]}-dimensional but the "
                f"corpus index is {self.index.d}-dimensional. Re-process the "
                "knowledge documents with the current embedding model or "
                "align the model with the corpus."
            )
        faiss.normalize_L2(query_emb.reshape(1, -1))
        search_k = min(
            len(self.chunks),
            max(top_k * 4, fallback_top_k, 10),
        )
        scores, indices = self.index.search(
            query_emb.reshape(1, -1),
            search_k,
        )
        scores, indices = scores[0], indices[0]
        max_score = scores[0] if len(scores) else 0.0
        query_terms = self._query_terms(query)
        candidates = []

        for score, idx in zip(scores, indices):
            if idx < 0:
                continue
            text = self.chunks[idx]
            lexical_score = self._lexical_score(query_terms, text)
            if score < abs_min_score and lexical_score == 0:
                continue
            if score < max_score * rel_score_drop and lexical_score == 0:
                continue
            candidates.append(
                {
                    "text": text,
                    "score": float(score) + lexical_score,
                    "vector_score": float(score),
                    "metadata": self.metadata[idx],
                }
            )

        candidates.sort(key=lambda item: item["score"], reverse=True)
        if candidates:
            return candidates[:top_k]

        return [
            {
                "text": self.chunks[idx],
                "score": float(scores[pos]),
                "vector_score": float(scores[pos]),
                "metadata": self.metadata[idx],
            }
            for pos, idx in enumerate(indices[:fallback_top_k])
            if idx >= 0
        ]

    @staticmethod
    def _normalize_for_match(value: str) -> str:
        return (
            value.replace("ی", "ي")
            .replace("ى", "ي")
            .replace("ک", "ك")
            .replace("\u200c", "")
            .lower()
        )

    @classmethod
    def _query_terms(cls, query: str) -> List[str]:
        stop_words = {
            "است", "هست", "برای", "چطور", "چیست", "میشه", "توانم",
            "شود", "یک", "این", "آن", "را", "به",
        }
        normalized = cls._normalize_for_match(query)
        return [
            term for term in normalized.split()
            if len(term) >= 3 and term not in stop_words
        ]

    @classmethod
    def _lexical_score(cls, query_terms: List[str], text: str) -> float:
        if not query_terms:
            return 0.0
        normalized_text = cls._normalize_for_match(text)
        matched = sum(1 for term in query_terms if term in normalized_text)
        return matched * 0.20
