"""
Firebase Auth + Supabase
========================
- Verifies Firebase JWT tokens on every request
- Provides get_current_user dependency for all routes
- Manages Supabase client (service role — backend only)
"""

from __future__ import annotations

import json
import logging
import os

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# ── Firebase Admin init ──────────────────────────────────────────────

def _init_firebase() -> None:
    if firebase_admin._apps:
        return  # already initialised
    sa = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")
    if not sa:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env var is not set")
    try:
        sa_dict = json.loads(sa)
        cred = credentials.Certificate(sa_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Invalid FIREBASE_SERVICE_ACCOUNT JSON: {e}")
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialised (project: %s)", sa_dict.get("project_id"))


_init_firebase()

# ── Supabase client (service role — never expose to frontend) ────────

def _init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


_supabase: Client = _init_supabase()


def get_supabase() -> Client:
    """FastAPI dependency — returns the shared Supabase service-role client."""
    return _supabase


# ── JWT verification ─────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency. Verifies the Firebase JWT and returns the decoded token.

    Usage:
        @router.get("/something")
        def handler(user: dict = Depends(get_current_user)):
            user_id = user["uid"]
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    token = credentials.credentials
    try:
        decoded = firebase_auth.verify_id_token(token, check_revoked=True)
        return decoded
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except firebase_auth.InvalidIdTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")
    except Exception as e:
        logger.exception("Token verification failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict | None:
    """Same as get_current_user but returns None instead of raising for unauthenticated requests."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
