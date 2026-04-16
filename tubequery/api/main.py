"""
TubeQuery API
=============
FastAPI backend. Run with:
    uvicorn api.main:app --reload

from the tubequery/ directory.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import chat, ingest, sources
from api.schemas import HealthResponse
import config

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="TubeQuery API",
    description="YouTube RAG backend — ingest videos, ask questions, get cited answers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────
# In production, replace "*" with your Next.js domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Create data dirs on startup ──────────────────────────────────────
os.makedirs(config.CHROMA_DIR, exist_ok=True)
os.makedirs(config.DATA_DIR, exist_ok=True)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(sources.router)


# ── Health check ─────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    return HealthResponse(status="ok")
