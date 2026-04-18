"""
API Schemas
===========
Pydantic models for all request and response bodies.
"""

from __future__ import annotations
import re
from pydantic import BaseModel, Field, validator


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
    source_title: str = ""
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
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        
        # Length limit
        if len(v) > 2000:
            raise ValueError('Question too long (max 2000 characters)')
        
        # Basic prompt injection patterns
        suspicious_patterns = [
            r'ignore\s+(?:previous|all|above|prior)\s+(?:instructions?|prompts?|rules?)',
            r'forget\s+(?:everything|all|previous|above)',
            r'you\s+are\s+now\s+(?:a|an)\s+\w+',
            r'act\s+as\s+(?:a|an)\s+\w+',
            r'pretend\s+(?:to\s+be|you\s+are)',
            r'roleplay\s+as',
            r'system\s*:',
            r'assistant\s*:',
            r'human\s*:',
            r'<\s*/?system\s*>',
            r'<\s*/?assistant\s*>',
            r'<\s*/?human\s*>',
            r'\\n\\n(?:system|assistant|human)\s*:',
        ]
        
        v_lower = v.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, v_lower, re.IGNORECASE):
                raise ValueError('Invalid input detected')
        
        return v.strip()
    
    @validator('kb_id')
    def validate_kb_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid knowledge base name')
        return v


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
