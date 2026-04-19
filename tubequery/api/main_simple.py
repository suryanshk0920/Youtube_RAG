"""
Simplified TubeQuery API for Render deployment
==============================================
This version removes complex startup logic to ensure port binding works.
Services are initialized lazily on first request.
"""

from __future__ import annotations

import logging
import os

# Apply memory optimizations first
from optimize_startup import optimize_for_low_memory
optimize_for_low_memory()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import chat, ingest, sources
from api.routers import sessions
from api.routers import profile
from api.routers import kbs
from api.routers import subscription
from api.schemas import HealthResponse

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="TubeQuery API",
    description="YouTube RAG backend — ingest videos, ask questions, get cited answers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiting (disabled for startup stability) ──────────────────
# app.add_middleware(RedisRateLimitMiddleware, default_requests_per_minute=60)
# Rate limiting will be handled by individual routes if needed

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(sources.router)
app.include_router(sessions.router)
app.include_router(profile.router)
app.include_router(kbs.router)
app.include_router(subscription.router)

# ── Health check ─────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    return HealthResponse(status="ok")

@app.get("/health/firebase", tags=["health"])
def firebase_health():
    """Check Firebase initialization status."""
    from api.auth import get_firebase_status
    return get_firebase_status()

@app.get("/", tags=["root"])
def root():
    return {
        "message": "TubeQuery API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

logger.info("🎉 TubeQuery API initialized - ready to serve requests")