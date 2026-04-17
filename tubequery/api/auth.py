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

from dotenv import load_dotenv
load_dotenv()  # ensure .env is loaded before reading env vars

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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

# ── Supabase HTTP client (no supabase package — uses httpx directly) ─

import httpx as _httpx

class _SupabaseDB:
    """
    Minimal Supabase PostgREST client using httpx.
    Only implements what we need: select, insert, upsert, update, delete.
    """
    def __init__(self, url: str, key: str):
        self._base = f"{url}/rest/v1"
        self._headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def table(self, name: str) -> "_TableQuery":
        return _TableQuery(self._base, self._headers, name)


class _TableQuery:
    def __init__(self, base: str, headers: dict, table: str):
        self._base = base
        self._headers = headers
        self._table = table
        self._filters: list[str] = []
        self._select_cols = "*"
        self._order: str | None = None
        self._count: str | None = None
        self._single = False

    def select(self, cols: str = "*", count: str | None = None) -> "_TableQuery":
        self._select_cols = cols
        self._count = count
        return self

    def eq(self, col: str, val) -> "_TableQuery":
        self._filters.append(f"{col}=eq.{val}")
        return self

    def gte(self, col: str, val) -> "_TableQuery":
        self._filters.append(f"{col}=gte.{val}")
        return self

    def order(self, col: str, desc: bool = False) -> "_TableQuery":
        self._order = f"{col}.{'desc' if desc else 'asc'}"
        return self

    def single(self) -> "_TableQuery":
        self._single = True
        return self

    def _url(self) -> str:
        params = [f"select={self._select_cols}"]
        params.extend(self._filters)
        if self._order:
            params.append(f"order={self._order}")
        return f"{self._base}/{self._table}?{'&'.join(params)}"

    def execute(self) -> "_Result":
        headers = dict(self._headers)
        if self._single:
            headers["Accept"] = "application/vnd.pgrst.object+json"
        if self._count:
            headers["Prefer"] = f"count={self._count}"
        resp = _httpx.get(self._url(), headers=headers, timeout=10.0)
        resp.raise_for_status()
        if self._single:
            data = resp.json() if resp.text else None
            return _Result(data=[data] if data else [], count=None)
        data = resp.json() if resp.text else []
        count = None
        if self._count and "content-range" in resp.headers:
            try:
                count = int(resp.headers["content-range"].split("/")[-1])
            except Exception:
                pass
        return _Result(data=data, count=count)

    def insert(self, data: dict) -> "_WriteQuery":
        return _WriteQuery(self._base, self._headers, self._table, "POST", data)

    def upsert(self, data: dict, on_conflict: str = "") -> "_WriteQuery":
        headers = dict(self._headers)
        headers["Prefer"] = f"resolution=merge-duplicates,return=representation"
        if on_conflict:
            headers["Prefer"] += f",on_conflict={on_conflict}"
        return _WriteQuery(self._base, headers, self._table, "POST", data)

    def update(self, data: dict) -> "_FilteredWrite":
        return _FilteredWrite(self._base, self._headers, self._table, "PATCH", data, self._filters)

    def delete(self) -> "_FilteredWrite":
        return _FilteredWrite(self._base, self._headers, self._table, "DELETE", None, self._filters)


class _WriteQuery:
    def __init__(self, base, headers, table, method, data):
        self._base = base
        self._headers = headers
        self._table = table
        self._method = method
        self._data = data

    def execute(self) -> "_Result":
        url = f"{self._base}/{self._table}"
        resp = _httpx.request(self._method, url, headers=self._headers, json=self._data, timeout=10.0)
        resp.raise_for_status()
        data = resp.json() if resp.text else []
        if isinstance(data, dict):
            data = [data]
        return _Result(data=data, count=None)


class _FilteredWrite:
    def __init__(self, base, headers, table, method, data, filters):
        self._base = base
        self._headers = headers
        self._table = table
        self._method = method
        self._data = data
        self._filters = filters

    def eq(self, col: str, val) -> "_FilteredWrite":
        self._filters = list(self._filters) + [f"{col}=eq.{val}"]
        return self

    def execute(self) -> "_Result":
        params = "&".join(self._filters)
        url = f"{self._base}/{self._table}?{params}"
        resp = _httpx.request(self._method, url, headers=self._headers, json=self._data, timeout=10.0)
        resp.raise_for_status()
        data = resp.json() if resp.text else []
        if isinstance(data, dict):
            data = [data]
        return _Result(data=data, count=None)


class _Result:
    def __init__(self, data: list, count):
        self.data = data
        self.count = count


def _init_supabase() -> _SupabaseDB:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return _SupabaseDB(url, key)


_supabase_db: _SupabaseDB = _init_supabase()


def get_supabase() -> _SupabaseDB:
    """FastAPI dependency — returns the shared Supabase DB client."""
    return _supabase_db


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
