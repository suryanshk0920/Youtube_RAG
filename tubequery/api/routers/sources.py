"""
Sources Router — auth-protected, user-scoped
"""
from __future__ import annotations
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from api.auth import get_current_user, get_supabase
from api.dependencies import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
def list_sources(
    kb_id: str | None = Query(None),
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """List sources for the current user only."""
    rows = db.table("sources").select("*").eq("user_id", user["uid"])
    if kb_id:
        # Filter by kb_name (the string name), not the UUID
        rows = rows.eq("kb_name", kb_id)
    result = rows.order("created_at", desc=True).execute()
    return result.data or []


@router.delete("/{source_id}", status_code=403)
def delete_source(
    source_id: str,
    kb_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
    vector_store=Depends(get_vector_store),
):
    """Delete source endpoint disabled to prevent usage manipulation."""
    raise HTTPException(
        status_code=403, 
        detail="Video deletion is disabled. Videos remain in your library permanently to ensure fair usage tracking."
    )


@router.get("/stats/{kb_id}")
def kb_stats(
    kb_id: str,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
    vector_store=Depends(get_vector_store),
):
    result = db.table("sources").select("video_count, chunk_count, created_at").eq("user_id", user["uid"]).eq("kb_id", kb_id).execute()
    rows = result.data or []
    return {
        "kb_id": kb_id,
        "source_count": len(rows),
        "video_count": sum(r.get("video_count", 0) for r in rows),
        "chunk_count": vector_store.count(kb_id),
        "last_updated": max((r["created_at"] for r in rows), default=None),
    }
