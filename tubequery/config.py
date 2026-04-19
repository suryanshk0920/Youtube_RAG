"""
TubeQuery Configuration
=======================
Central configuration file. All constants live here — nothing is
hardcoded anywhere else in the codebase. Values are loaded from
environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load Environment ────────────────────────────────────────────────
load_dotenv()

# ── API Keys ────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# ── Paths ───────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: str = os.getenv("DATA_DIR", str(BASE_DIR / "data"))
CHROMA_DIR: str = os.getenv("CHROMA_DIR", str(BASE_DIR / "data" / "chromadb"))
SOURCES_FILE: str = os.path.join(DATA_DIR, "sources.json")

# ── Chunking Settings ──────────────────────────────────────────────
CHUNK_SIZE: int = 80            # target words per chunk
CHUNK_OVERLAP: int = 15         # overlap between consecutive chunks (words)

# ── Retrieval Settings ─────────────────────────────────────────────
TOP_K: int = 8                  # chunks to retrieve per query
MIN_RELEVANCE_SCORE: float = 0.0  # accept all retrieved chunks, let LLM decide relevance

# ── Embedding Model ────────────────────────────────────────────────
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# ── LLM Settings ───────────────────────────────────────────────────
GEMINI_MODEL: str = "gemini-2.0-flash"
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
MAX_CONTEXT_TOKENS: int = 8000
CONVERSATION_HISTORY_TURNS: int = 10

# ── LLM Provider ───────────────────────────────────────────────────
# Set to "gemini" or "openrouter"
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")

# ── ChromaDB ────────────────────────────────────────────────────────
COLLECTION_PREFIX: str = "tubequery_kb_"

# ── Redis (Upstash) ─────────────────────────────────────────────────
UPSTASH_REDIS_URL: str = os.getenv("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN: str = os.getenv("UPSTASH_REDIS_TOKEN", "")
UPSTASH_REDIS_REST_URL: str = os.getenv("UPSTASH_REDIS_REST_URL", "")
REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
REDIS_RETRY_ON_TIMEOUT: bool = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"

# ── Redis Key Patterns ─────────────────────────────────────────────
REDIS_USAGE_KEY_PREFIX: str = "usage:"
REDIS_RATE_LIMIT_KEY_PREFIX: str = "rate_limit:"
REDIS_SESSION_KEY_PREFIX: str = "session:"
REDIS_JOB_QUEUE_KEY: str = "job_queue"

# ── Usage Tracking Settings ────────────────────────────────────────
USAGE_RESET_HOUR: int = 0  # UTC hour when daily usage resets (midnight)
USAGE_TTL_SECONDS: int = 86400 * 2  # 2 days TTL for usage data

# ── Redis Cost Optimization ───────────────────────────────────────
REDIS_COST_OPTIMIZATION: bool = os.getenv("REDIS_COST_OPTIMIZATION", "true").lower() == "true"
REDIS_CACHE_TTL_SECONDS: int = int(os.getenv("REDIS_CACHE_TTL_SECONDS", "10"))
REDIS_BATCH_OPERATIONS: bool = os.getenv("REDIS_BATCH_OPERATIONS", "true").lower() == "true"
REDIS_RATE_LIMIT_CACHE_TTL: int = int(os.getenv("REDIS_RATE_LIMIT_CACHE_TTL", "10"))
