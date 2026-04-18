"""
Embedding Service
=================
Abstract interface for text embedding, plus a concrete local
implementation using sentence-transformers MiniLM.

To swap providers, create a new class inheriting EmbeddingService
and update the service initialisation in app.py.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from sentence_transformers import SentenceTransformer

import config

logger = logging.getLogger(__name__)


# ── Interface ───────────────────────────────────────────────────────
class EmbeddingService(ABC):
    """Base class for all embedding implementations."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts. Returns list of float vectors."""

    @abstractmethod
    def embed_single(self, text: str) -> list[float]:
        """Embed a single text string. Returns one float vector."""


# ── MiniLM Implementation ──────────────────────────────────────────
class MiniLMEmbeddingService(EmbeddingService):
    """
    Local embeddings using sentence-transformers all-MiniLM-L6-v2.
    Includes an in-memory LRU cache for single embeddings (queries).
    """

    def __init__(self) -> None:
        logger.info("Loading embedding model: %s", config.EMBEDDING_MODEL)
        self._model = SentenceTransformer(config.EMBEDDING_MODEL)
        self._cache: dict[str, list[float]] = {}  # simple in-memory cache
        self._cache_max = 1000  # max cached queries
        logger.info("Embedding model loaded successfully.")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts, batch_size=64, show_progress_bar=False
        )
        return vectors.tolist()

    def embed_single(self, text: str) -> list[float]:
        # Check cache first
        if text in self._cache:
            return self._cache[text]
        result = self.embed([text])[0]
        # Evict oldest if at capacity
        if len(self._cache) >= self._cache_max:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[text] = result
        return result


# ── Future implementations (swap in app.py to use) ─────────────────
# class OpenAIEmbeddingService(EmbeddingService): ...
# class CohereEmbeddingService(EmbeddingService): ...
