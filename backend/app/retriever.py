"""In-memory TF-IDF retriever.

Deliberately dependency-light: no external vector DB or embedding API call,
which keeps sensitive document text off third-party services until a query
explicitly forwards selected chunks. Swap for a vector store when scaling.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .chunker import Chunk


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


class DocumentIndex:
    def __init__(self, doc_id: str, filename: str, state: str | None, chunks: list[Chunk]):
        self.doc_id = doc_id
        self.filename = filename
        self.state = state
        self.chunks = chunks
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_df=0.95,
            min_df=1,
        )
        if chunks:
            self._matrix = self._vectorizer.fit_transform([c.text for c in chunks])
        else:
            self._matrix = None

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not self.chunks or self._matrix is None or not query.strip():
            return []
        q = self._vectorizer.transform([query])
        # cosine similarity (TF-IDF rows are L2-normalized by default)
        sims = (self._matrix @ q.T).toarray().ravel()
        idx = np.argsort(-sims)[:top_k]
        return [
            RetrievedChunk(chunk=self.chunks[i], score=float(sims[i]))
            for i in idx
            if sims[i] > 0
        ]


class IndexStore:
    def __init__(self) -> None:
        self._docs: dict[str, DocumentIndex] = {}

    def add(self, index: DocumentIndex) -> None:
        self._docs[index.doc_id] = index

    def get(self, doc_id: str) -> DocumentIndex | None:
        return self._docs.get(doc_id)

    def list(self) -> list[DocumentIndex]:
        return list(self._docs.values())

    def remove(self, doc_id: str) -> bool:
        return self._docs.pop(doc_id, None) is not None


store = IndexStore()
