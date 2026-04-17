"""
Database Layer
==============
All Supabase operations. Single source of truth for DB access.
Uses the service-role client — all writes are trusted (auth enforced at API layer).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── User profiles ────────────────────────────────────────────────────

def upsert_user(db: Any, user_id: str, email: str | None = None) -> dict:
    """Create or update a user profile. Called on every authenticated request."""
    data = {"id": user_id}
    if email:
        data["email"] = email
    result = db.table("user_profiles").upsert(data, on_conflict="id").execute()
    return result.data[0] if result.data else data


def get_user(db: Any, user_id: str) -> dict | None:
    result = db.table("user_profiles").select("*").eq("id", user_id).execute()
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
    result = db.table("knowledge_bases").select("*").eq("user_id", user_id).order("created_at").execute()
    return result.data or []


def delete_kb(db: Any, kb_id: str, user_id: str) -> None:
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
        "source_type": source.source_type.value,
        "status": source.status.value,
        "video_count": source.video_count,
        "chunk_count": source.chunk_count,
        "error_message": source.error_message or "",
    }
    result = db.table("sources").upsert(data, on_conflict="id").execute()
    return result.data[0] if result.data else {}


def list_sources(db: Any, user_id: str, kb_id: str | None = None) -> list[dict]:
    query = db.table("sources").select("*").eq("user_id", user_id)
    if kb_id:
        query = query.eq("kb_id", kb_id)
    result = query.order("created_at", desc=True).execute()
    return result.data or []


def get_source(db: Any, source_id: str, user_id: str) -> dict | None:
    result = db.table("sources").select("*").eq("id", source_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def delete_source(db: Any, source_id: str, user_id: str) -> None:
    db.table("sources").delete().eq("id", source_id).eq("user_id", user_id).execute()


# ── Chat sessions ────────────────────────────────────────────────────

def list_sessions(db: Any, user_id: str) -> list[dict]:
    result = (
        db.table("chat_sessions")
        .select("id, source_id, source_title, kb_name, messages, created_at, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data or []


def get_session(db: Any, session_id: str, user_id: str) -> dict | None:
    result = (
        db.table("chat_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


def create_session(db: Any, user_id: str, source_id: str, source_title: str, kb_name: str) -> dict:
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
    result = (
        db.table("chat_sessions")
        .update({"messages": messages, "updated_at": "now()"})
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def delete_session(db: Any, session_id: str, user_id: str) -> None:
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
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    # Select just the id column and count the rows returned
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
    "free":  {"ingest": 5,   "chat": 50},
    "pro":   {"ingest": 100, "chat": -1},   # -1 = unlimited
    "team":  {"ingest": -1,  "chat": -1},
}


def check_limit(db: Any, user_id: str, event_type: str) -> None:
    """
    Raises HTTPException 402 if the user has exceeded their plan limit.
    Call before any billable operation.
    """
    from fastapi import HTTPException
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
