"""
API Schemas
===========
Pydantic models for all request and response bodies.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Ingest ──────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    url: str = Field(..., description="YouTube video or playlist URL")
    kb_id: str = Field("default", description="Knowledge base to ingest into")


class IngestResponse(BaseModel):
    source_id: str
    title: str
    kb_id: str
    video_count: int
    chunk_count: int
    status: str


# ── Intro ───────────────────────────────────────────────────────────

class IntroResponse(BaseModel):
    source_id: str
    intro: str
    topics: list[str]
    questions: list[str]


# ── Chat ────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str                          # "user" or "assistant"
    content: str
    reasoning_details: list | None = None  # preserved for OpenRouter multi-turn


class ChatRequest(BaseModel):
    question: str
    kb_id: str = "default"
    history: list[ChatMessage] = Field(default_factory=list)
    source_ids: list[str] | None = None  # None = search all sources in KB


class CitationOut(BaseModel):
    video_title: str
    video_id: str
    timestamp_label: str
    youtube_url: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    found_relevant_content: bool


# ── Sources ─────────────────────────────────────────────────────────

class SourceOut(BaseModel):
    id: str
    title: str
    url: str
    source_type: str
    kb_id: str
    status: str
    video_count: int
    chunk_count: int
    created_at: str


# ── Health ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
