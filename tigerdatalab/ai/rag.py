"""Dependency-light retrieval layer for company knowledge.

This module provides deterministic chunking and lexical retrieval without
forcing a vector database or embedding dependency on every TigerDataLab user.
Embedding/vector stores can be layered on top through the same document API.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into stable word-boundary chunks."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be > 0 and 0 <= overlap < chunk_size")
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        current: list[str] = []
        length = 0
        i = start
        while i < len(words) and (not current or length + len(words[i]) + 1 <= chunk_size):
            current.append(words[i])
            length += len(words[i]) + (1 if current else 0)
            i += 1
        if not current:
            current = [words[start]]
            i = start + 1
        chunks.append(" ".join(current))
        if i >= len(words):
            break
        consumed = max(1, len(current))
        overlap_words = max(0, min(consumed - 1, int(consumed * overlap / max(1, length))))
        start = i - overlap_words
    return chunks


class KnowledgeBase:
    """In-memory knowledge base with deterministic lexical retrieval."""

    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}
        self.chunks: list[Chunk] = []

    def add(self, documents: Document | Iterable[Document], *, chunk_size: int = 800, overlap: int = 100) -> None:
        items = [documents] if isinstance(documents, Document) else list(documents)
        for doc in items:
            self.documents[doc.id] = doc
            self.chunks = [c for c in self.chunks if c.document_id != doc.id]
            for idx, text in enumerate(chunk_text(doc.text, chunk_size, overlap)):
                self.chunks.append(Chunk(f"{doc.id}:{idx}", doc.id, text, dict(doc.metadata)))

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        if top_k <= 0:
            return []
        terms = {t for t in re.findall(r"[a-z0-9_]+", query.lower()) if len(t) > 1}
        if not terms:
            return []
        ranked: list[tuple[Chunk, float]] = []
        for chunk in self.chunks:
            words = re.findall(r"[a-z0-9_]+", chunk.text.lower())
            if not words:
                continue
            unique = set(words)
            score = sum(1 for term in terms if term in unique) / len(terms)
            if score:
                ranked.append((chunk, score))
        ranked.sort(key=lambda item: (-item[1], item[0].id))
        return ranked[:top_k]

    def context(self, query: str, top_k: int = 5) -> str:
        """Build a compact context block suitable for an LLM prompt."""
        return "\n\n".join(item.text for item, _ in self.search(query, top_k))
