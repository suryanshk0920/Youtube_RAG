"""
Sessions Router
===============
CRUD for chat sessions stored in Supabase.
All endpoints require authentication.
"""

from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from api.auth import get_current_user, get_supabase
from api.db import (
    create_session,
    delete_session,
    get_session,
    list_sessions,
    update_session_messages,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    source_id: str
    source_title: str
    kb_name: str


class UpdateSessionRequest(BaseModel):
    messages: list[Any]


@router.get("")
def get_sessions(
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """List all chat sessions for the current user."""
    return list_sessions(db, user["uid"])


@router.post("", status_code=201)
def post_session(
    body: CreateSessionRequest,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """Create a new chat session."""
    return create_session(db, user["uid"], body.source_id, body.source_title, body.kb_name)


@router.patch("/{session_id}")
def patch_session(
    session_id: str,
    body: UpdateSessionRequest,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """Update messages in a session."""
    return update_session_messages(db, session_id, user["uid"], body.messages)


@router.delete("/{session_id}", status_code=204)
def del_session(
    session_id: str,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
):
    """Delete a session."""
    existing = get_session(db, session_id, user["uid"])
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(db, session_id, user["uid"])
