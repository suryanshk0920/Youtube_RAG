"""
Profile Router
==============
GET  /profile  — current user's profile + usage stats
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from api.auth import get_current_user, get_supabase
from api.db_orm import get_monthly_usage, get_user, upsert_user, PLAN_LIMITS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
def get_profile(
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """Return the current user's profile and usage stats."""
    uid = user["uid"]
    email = user.get("email", "")

    # Upsert ensures the profile exists
    profile = upsert_user(db, uid, email)
    plan = profile.get("plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    # Monthly usage
    ingest_used = get_monthly_usage(db, uid, "ingest")
    chat_used = get_monthly_usage(db, uid, "chat")

    return {
        "uid": uid,
        "email": email,
        "display_name": user.get("name", ""),
        "photo_url": user.get("picture", ""),
        "plan": plan,
        "created_at": profile.get("created_at", ""),
        "usage": {
            "ingest": {
                "used": ingest_used,
                "limit": limits.get("ingest", 5),
            },
            "chat": {
                "used": chat_used,
                "limit": limits.get("chat", 50),
            },
        },
    }
