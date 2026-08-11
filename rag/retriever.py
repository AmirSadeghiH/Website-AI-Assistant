import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from rag.embeddings import Embedder


import sys
import io

# تنظیم encoding برای خروجی و ورودی
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')


class Retriever:
    """
    FAISS-based retriever for Persian RAG.
    Uses precomputed chunks, embeddings, and metadata.
    """

    def __init__(
        self,
        chunks_path: str = "./Data/chunks.json",
        metadata_path: str = "./Data/metadata.json",
        embeddings_path: str = "./Data/embeddings.npy",
        device: Optional[str] = None,
        normalize: bool = True,
    ):
        # Load chunks
        with open(chunks_path, "r", encoding="utf-8") as f:
            self.chunks: List[str] = json.load(f)

        # Load metadata
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata: List[Dict] = json.load(f)

        # Load embeddings
        self.embeddings: np.ndarray = np.load(embeddings_path).astype("float32")
        assert len(self.chunks) == self.embeddings.shape[0], "Chunks and embeddings count mismatch"

        # Normalize for cosine similarity
        if normalize:
            faiss.normalize_L2(self.embeddings)

        # FAISS index
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity if normalized
        self.index.add(self.embeddings)

        # Embedder for queries
        self.embedder = Embedder(device=device)

        print(f"[Retriever] Loaded {len(self.chunks)} chunks with metadata and embeddings")

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        abs_min_score: float = 0.10,
        rel_score_drop: float = 0.4,
        fallback_top_k: int = 5,
    ) -> List[Dict]:
        """
        Retrieve top_k relevant chunks for a query.
        Returns list of dicts: {text, score, metadata}
        """
        print(f"[DEBUG] Retrieving for query: {query}")
        query_emb = self.embedder.embed_query_api(query).astype("float32")
        faiss.normalize_L2(query_emb.reshape(1, -1))

        scores, indices = self.index.search(query_emb.reshape(1, -1), self.chunks.__len__())
        scores, indices = scores[0], indices[0]

        max_score = scores[0] if scores.size > 0 else 0.0
        candidates = []
        query_terms = self._query_terms(query)

        for score, idx in zip(scores, indices):
            text = self.chunks[idx]
            lexical_score = self._lexical_score(query_terms, text)
            if score < abs_min_score and lexical_score == 0:
                continue
            if score < max_score * rel_score_drop and lexical_score == 0:
                continue
            candidates.append({
                "text": text,
                "score": float(score) + lexical_score,
                "vector_score": float(score),
                "metadata": self.metadata[idx],
            })

        candidates.sort(key=lambda item: item["score"], reverse=True)
        results = candidates[:top_k]

        # Fallback: if no results pass threshold, take top fallback_top_k
        if len(results) == 0:
            for i in range(min(fallback_top_k, len(indices))):
                idx = indices[i]
                results.append({
                    "text": self.chunks[idx],
                    "score": float(scores[i]),
                    "vector_score": float(scores[i]),
                    "metadata": self.metadata[idx],
                })

        return results

    @staticmethod
    def _normalize_for_match(value: str) -> str:
        return (
            value.replace("ي", "ی")
            .replace("ى", "ی")
            .replace("ك", "ک")
            .replace("\u200c", "")
            .replace("‌", "")
            .lower()
        )

    @classmethod
    def _query_terms(cls, query: str) -> List[str]:
        stop_words = {
            "است", "هست", "چیه", "چیست", "برای", "چطور", "چگونه",
            "می", "توانم", "شود", "یک", "این", "آن", "را", "به",
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
        # A small boost keeps vector similarity primary while rescuing
        # exact business terms such as «ارسال» and «بلوکارت».
        return matched * 0.20


if __name__ == "__main__":
    retriever = Retriever()
    query = "ثبت‌نام دانشجوی مهمان"
    top_chunks = retriever.retrieve(query)
    for c in top_chunks:
        print(f"Score: {c['score']:.3f}, Text: {c['text'][:100]}...")
