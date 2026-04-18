"""
Knowledge Bases Router
======================
GET    /kbs        — list user's KBs (auto-creates 'default' if none)
POST   /kbs        — create a new KB
DELETE /kbs/{id}   — delete a KB and all its sources/sessions
"""
from __future__ import annotations
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import get_current_user, get_supabase
from api.db import PLAN_LIMITS, get_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kbs", tags=["knowledge_bases"])


class CreateKBRequest(BaseModel):
    name: str


@router.get("")
def list_kbs(
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """List KBs for the current user. Auto-creates 'default' if none exist."""
    uid = user["uid"]
    result = db.table("knowledge_bases").select("*").eq("user_id", uid).order("created_at").execute()
    kbs = result.data or []

    # Auto-create default KB on first login
    if not kbs:
        created = db.table("knowledge_bases").insert({"user_id": uid, "name": "default"}).execute()
        kbs = created.data or []

    return kbs


@router.post("", status_code=201)
def create_kb(
    body: CreateKBRequest,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """Create a new KB. Enforces plan limits."""
    uid = user["uid"]
    name = body.name.strip().lower().replace(" ", "_")

    if not name:
        raise HTTPException(status_code=400, detail="Library name cannot be empty")

    # Check plan limit
    profile = get_user(db, uid)
    plan = profile.get("plan", "free") if profile else "free"
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    kb_limit = limits.get("kbs", 2)

    if kb_limit != -1:
        existing = db.table("knowledge_bases").select("id").eq("user_id", uid).execute()
        if len(existing.data or []) >= kb_limit:
            raise HTTPException(
                status_code=402,
                detail=f"Free plan allows {kb_limit} libraries. Upgrade to Pro for unlimited."
            )

    # Check duplicate name
    dup = db.table("knowledge_bases").select("id").eq("user_id", uid).eq("name", name).execute()
    if dup.data:
        raise HTTPException(status_code=409, detail=f"Library '{name}' already exists")

    result = db.table("knowledge_bases").insert({"user_id": uid, "name": name}).execute()
    return result.data[0]


@router.delete("/{kb_id}", status_code=204)
def delete_kb(
    kb_id: str,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """Delete a KB. Cannot delete 'default'."""
    uid = user["uid"]
    kb = db.table("knowledge_bases").select("*").eq("id", kb_id).eq("user_id", uid).execute()
    if not kb.data:
        raise HTTPException(status_code=404, detail="Library not found")
    if kb.data[0]["name"] == "default":
        raise HTTPException(status_code=400, detail="Cannot delete the default library")
    db.table("knowledge_bases").delete().eq("id", kb_id).eq("user_id", uid).execute()
