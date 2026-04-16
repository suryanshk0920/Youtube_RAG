"""
Vector Store Service
====================
Abstract interface for vector storage, plus a concrete ChromaDB
implementation that persists locally.

Each knowledge base gets its own ChromaDB collection, enabling
complete isolation between different content libraries.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import chromadb

import config
from models.chunk import Chunk

logger = logging.getLogger(__name__)


# ── Interface ───────────────────────────────────────────────────────
class VectorStore(ABC):
    """Base class for all vector store implementations."""

    @abstractmethod
    def upsert(
        self, chunks: list[Chunk], embeddings: list[list[float]], kb_id: str = ""
    ) -> None:
        """Store chunks and their embeddings."""

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        kb_id: str,
        top_k: int = 5,
        source_id: str | None = None,
    ) -> list[tuple[Chunk, float]]:
        """
        Return top_k most similar chunks for a query embedding.
        Optionally filter by source_id to scope to a single video.
        Returns list of (Chunk, similarity_score) tuples.
        """

    @abstractmethod
    def delete_source(self, source_id: str, kb_id: str) -> None:
        """Remove all chunks belonging to a source from a knowledge base."""

    @abstractmethod
    def count(self, kb_id: str) -> int:
        """Return total number of chunks in a knowledge base."""


# ── ChromaDB Implementation ────────────────────────────────────────
class ChromaVectorStore(VectorStore):
    """
    Local ChromaDB implementation.

    - Persists to ``config.CHROMA_DIR``.
    - Each knowledge base is a separate ChromaDB collection.
    - Collection naming: ``tubequery_kb_{kb_id}``
    - Uses cosine similarity for nearest-neighbour search.
    """

    def __init__(self) -> None:
        logger.info("Initialising ChromaDB at: %s", config.CHROMA_DIR)
        self._client = chromadb.PersistentClient(path=config.CHROMA_DIR)

    # ── Helpers ─────────────────────────────────────────────────────
    def _collection(self, kb_id: str):
        """Get or create a collection for the given knowledge base."""
        name = f"{config.COLLECTION_PREFIX}{kb_id}"
        # chromadb >=1.x uses configuration= instead of metadata= for HNSW space
        try:
            return self._client.get_or_create_collection(
                name=name,
                configuration={"hnsw": {"space": "cosine"}},
            )
        except TypeError:
            # Fallback for older chromadb <1.x
            return self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )

    # ── Public API ──────────────────────────────────────────────────
    def upsert(
        self, chunks: list[Chunk], embeddings: list[list[float]], kb_id: str = ""
    ) -> None:
        if not chunks:
            return

        col = self._collection(kb_id)

        # IDs include source_id to prevent collisions between videos in the same KB
        ids = [f"{c.source_id}_{c.video_id}_{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.to_metadata() for c in chunks]

        col.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        kb_id: str,
        top_k: int = 5,
        source_id: str | None = None,
    ) -> list[tuple[Chunk, float]]:
        col = self._collection(kb_id)
        total = col.count()
        if total == 0:
            return []

        where = {"source_id": source_id} if source_id else None

        results = col.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, total),
            include=["documents", "metadatas", "distances"],
            where=where,
        )

        output: list[tuple[Chunk, float]] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunk = Chunk(
                text=doc,
                video_id=meta["video_id"],
                video_title=meta["video_title"],
                start_time=meta["start_time"],
                end_time=meta["end_time"],
                chunk_index=meta["chunk_index"],
                source_id=meta["source_id"],
            )
            # ChromaDB returns distance; convert to similarity
            similarity = 1.0 - dist
            output.append((chunk, similarity))

        return output

    def delete_source(self, source_id: str, kb_id: str) -> None:
        col = self._collection(kb_id)
        col.delete(where={"source_id": source_id})
        logger.info("Deleted source %s from KB %s", source_id, kb_id)

    def count(self, kb_id: str) -> int:
        try:
            return self._collection(kb_id).count()
        except Exception:
            return 0
