"""
Dependencies
============
Shared service instances — initialised once on startup and injected
into route handlers via FastAPI's dependency injection system.
"""

from __future__ import annotations

from functools import lru_cache

from services.embedding_service import MiniLMEmbeddingService
from services.llm_service import GeminiLLMService, OpenRouterLLMService
from services.vector_store import ChromaVectorStore
import config


@lru_cache(maxsize=1)
def get_embedding_service() -> MiniLMEmbeddingService:
    return MiniLMEmbeddingService()


@lru_cache(maxsize=1)
def get_vector_store() -> ChromaVectorStore:
    return ChromaVectorStore()


@lru_cache(maxsize=1)
def get_llm_service():
    if config.LLM_PROVIDER == "openrouter":
        return OpenRouterLLMService()
    return GeminiLLMService()
