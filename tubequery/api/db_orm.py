"""
ORM-based Database Layer
=======================
Provides the same interface as the old db.py but with better structure and type safety.
Uses the existing Supabase client for compatibility while providing ORM-like benefits.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ── User profiles ────────────────────────────────────────────────────

def upsert_user(db: Any, user_id: str, email: str | None = None) -> dict:
    """Create or update a user profile. Called on every authenticated request."""
    data = {"uid": user_id}  # Use 'uid' instead of 'id'
    if email:
        data["email"] = email
    result = db.table("user_profiles").upsert(data, on_conflict="uid").execute()
    return result.data[0] if result.data else data


def get_user(db: Any, user_id: str) -> dict | None:
    """Get user by ID."""
    result = db.table("user_profiles").select("*").eq("uid", user_id).execute()
    return result.data[0] if result.data else None

# ── Knowledge bases ──────────────────────────────────────────────────

def get_or_create_kb(db: Any, user_id: str, name: str) -> dict:
    """Get a KB by name, creating it if it doesn't exist."""
    result = db.table("knowledge_bases").select("*").eq("user_id", user_id).eq("name", name).execute()
    if result.data:
        return result.data[0]
    created = db.table("knowledge_bases").insert({"user_id": user_id, "name": name}).execute()
    return created.data[0]


def list_kbs(db: Any, user_id: str) -> list[dict]:
    """List all knowledge bases for a user."""
    result = db.table("knowledge_bases").select("*").eq("user_id", user_id).order("created_at").execute()
    return result.data or []


def delete_kb(db: Any, kb_id: str, user_id: str) -> None:
    """Delete a knowledge base."""
    db.table("knowledge_bases").delete().eq("id", kb_id).eq("user_id", user_id).execute()

# ── Sources ──────────────────────────────────────────────────────────

def save_source(db: Any, user_id: str, kb_id: str, source: Any) -> dict:
    """Insert or update a source record."""
    data = {
        "id": source.id,
        "user_id": user_id,
        "kb_id": kb_id,
        "url": source.url,
        "title": source.title,
        "source_type": source.source_type.value if hasattr(source.source_type, 'value') else str(source.source_type),
        "status": source.status.value if hasattr(source.status, 'value') else str(source.status),
        "video_count": source.video_count,
        "chunk_count": source.chunk_count,
        "error_message": source.error_message or "",
    }
    result = db.table("sources").upsert(data, on_conflict="id").execute()
    return result.data[0] if result.data else {}


def list_sources(db: Any, user_id: str, kb_id: str | None = None) -> list[dict]:
    """List sources for a user, optionally filtered by KB."""
    query = db.table("sources").select("*").eq("user_id", user_id)
    if kb_id:
        query = query.eq("kb_id", kb_id)
    result = query.order("created_at", desc=True).execute()
    return result.data or []


def get_source(db: Any, source_id: str, user_id: str) -> dict | None:
    """Get a specific source."""
    result = db.table("sources").select("*").eq("id", source_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def delete_source(db: Any, source_id: str, user_id: str) -> None:
    """Delete a source."""
    db.table("sources").delete().eq("id", source_id).eq("user_id", user_id).execute()

# ── Chat sessions ────────────────────────────────────────────────────

def list_sessions(db: Any, user_id: str) -> list[dict]:
    """List all chat sessions for a user."""
    result = (
        db.table("chat_sessions")
        .select("id, source_id, source_title, kb_name, messages, created_at, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data or []


def get_session(db: Any, session_id: str, user_id: str) -> dict | None:
    """Get a specific chat session."""
    result = (
        db.table("chat_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


def create_session(db: Any, user_id: str, source_id: str, source_title: str, kb_name: str) -> dict:
    """Create a new chat session."""
    data = {
        "user_id": user_id,
        "source_id": source_id,
        "source_title": source_title,
        "kb_name": kb_name,
        "messages": [],
    }
    result = db.table("chat_sessions").insert(data).execute()
    return result.data[0]


def update_session_messages(db: Any, session_id: str, user_id: str, messages: list) -> dict:
    """Update chat session messages."""
    result = (
        db.table("chat_sessions")
        .update({"messages": messages, "updated_at": "now()"})
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def delete_session(db: Any, session_id: str, user_id: str) -> None:
    """Delete a chat session."""
    db.table("chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()

# ── Usage tracking ───────────────────────────────────────────────────

def log_usage(db: Any, user_id: str, event_type: str, source_id: str | None = None, metadata: dict | None = None) -> None:
    """Fire-and-forget usage event logging."""
    try:
        db.table("usage_events").insert({
            "user_id": user_id,
            "event_type": event_type,
            "source_id": source_id,
            "metadata": metadata or {},
        }).execute()
    except Exception as e:
        logger.warning("Failed to log usage event: %s", e)


def get_monthly_usage(db: Any, user_id: str, event_type: str) -> int:
    """Count events of a given type in the current calendar month."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # Use Z suffix instead of +00:00 to avoid URL encoding issues
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = (
        db.table("usage_events")
        .select("id")
        .eq("user_id", user_id)
        .eq("event_type", event_type)
        .gte("created_at", month_start)
        .execute()
    )
    return len(result.data) if result.data else 0

# ── Plan limits ──────────────────────────────────────────────────────

PLAN_LIMITS = {
    "free":  {"ingest": 3,   "chat": 20,  "kbs": 2},
    "pro":   {"ingest": 50, "chat": 500,  "kbs": -1},
    "team":  {"ingest": -1,  "chat": -1,  "kbs": -1},
}


def check_limit(db: Any, user_id: str, event_type: str) -> None:
    """
    Raises HTTPException 402 if the user has exceeded their plan limit.
    Call before any billable operation.
    """
    user = get_user(db, user_id)
    if not user:
        return  # new user, allow
    plan = user.get("plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    limit = limits.get(event_type, 0)
    if limit == -1:
        return  # unlimited
    current = get_monthly_usage(db, user_id, event_type)
    if current >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "plan_limit_exceeded",
                "plan": plan,
                "event_type": event_type,
                "limit": limit,
                "current": current,
                "message": f"You've reached the {plan} plan limit of {limit} {event_type}s/month. Upgrade to continue.",
            }
        )