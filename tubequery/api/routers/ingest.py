"""
Ingest Router — auth-protected, user-scoped
"""
from __future__ import annotations
import json
import logging
from typing import Any, Generator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.auth import get_current_user, get_supabase
from api.db import check_limit, log_usage, upsert_user
from api.dependencies import get_embedding_service, get_llm_service, get_vector_store
from api.schemas import IngestRequest, IngestResponse, IntroResponse
from core.ingestion import ingest_url
from core.retriever import generate_intro

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


def _source_to_dict(source) -> dict:
    return {
        "source_id": source.id,
        "title": source.title,
        "kb_id": source.kb_id,
        "video_count": source.video_count,
        "chunk_count": source.chunk_count,
        "status": source.status.value,
    }


def _save_source_to_db(db: Any, user_id: str, source) -> None:
    """Persist source to Supabase."""
    db.table("sources").upsert({
        "id": source.id,
        "user_id": user_id,
        "kb_id": source.kb_id,
        "url": source.url,
        "title": source.title,
        "source_type": source.source_type.value,
        "status": source.status.value,
        "video_count": source.video_count,
        "chunk_count": source.chunk_count,
        "error_message": source.error_message or "",
    }, on_conflict="id").execute()


@router.post("/stream")
def ingest_stream(
    body: IngestRequest,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
):
    uid = user["uid"]
    upsert_user(db, uid, user.get("email", ""))

    # Deduplication — scoped to this user
    existing = db.table("sources").select("*").eq("user_id", uid).eq("url", body.url.strip()).execute()
    duplicate = next((s for s in (existing.data or []) if s.get("chunk_count", 0) > 0), None)

    if duplicate:
        def already_done():
            yield f"data: {json.dumps({'type': 'step', 'step': 'cached', 'detail': 'Already ingested'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'source': {'source_id': duplicate['id'], 'title': duplicate['title'], 'kb_id': duplicate['kb_id'], 'video_count': duplicate['video_count'], 'chunk_count': duplicate['chunk_count'], 'status': duplicate['status']}})}\n\n"
        return StreamingResponse(already_done(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # Check plan limits before ingesting
    try:
        check_limit(db, uid, "ingest")
    except HTTPException as e:
        def limit_error():
            yield f"data: {json.dumps({'type': 'error', 'detail': e.detail if isinstance(e.detail, str) else e.detail.get('message', 'Limit exceeded')})}\n\n"
        return StreamingResponse(limit_error(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    def event_stream() -> Generator[str, None, None]:
        try:
            steps = []

            def progress_callback(current: int, total: int, message: str) -> None:
                steps.append(f"data: {json.dumps({'type': 'progress', 'current': current, 'total': total, 'video': message})}\n\n")

            yield f"data: {json.dumps({'type': 'step', 'step': 'fetch', 'detail': 'Fetching transcript…'})}\n\n"

            source = ingest_url(
                url=body.url,
                kb_id=body.kb_id,
                embedding_service=embedding_service,
                vector_store=vector_store,
                progress_callback=progress_callback,
            )

            for s in steps:
                yield s

            if source.chunk_count == 0:
                yield f"data: {json.dumps({'type': 'error', 'detail': 'No transcript available. Captions may be disabled.'})}\n\n"
                return

            _save_source_to_db(db, uid, source)
            log_usage(db, uid, "ingest", source.id, {"title": source.title, "chunk_count": source.chunk_count})

            yield f"data: {json.dumps({'type': 'step', 'step': 'done', 'detail': f'{source.chunk_count} chunks indexed'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'source': _source_to_dict(source)})}\n\n"

        except Exception as e:
            logger.exception("Streaming ingestion failed")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/{source_id}/intro", response_model=IntroResponse)
def get_intro(
    source_id: str,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_supabase),
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
    llm_service=Depends(get_llm_service),
):
    # Verify source belongs to this user
    result = db.table("sources").select("*").eq("id", source_id).eq("user_id", user["uid"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Source not found")

    from models.source import Source, SourceType, IngestionStatus
    row = result.data[0]
    source = Source(
        id=row["id"], url=row["url"],
        source_type=SourceType(row["source_type"]),
        title=row["title"], kb_id=row["kb_id"],
        status=IngestionStatus(row["status"]),
        video_count=row["video_count"], chunk_count=row["chunk_count"],
    )

    try:
        data = generate_intro(source=source, embedding_service=embedding_service,
                              vector_store=vector_store, llm_service=llm_service)
        return IntroResponse(source_id=source_id, intro=data.get("intro", ""),
                             topics=data.get("topics", []), questions=data.get("questions", []))
    except Exception as e:
        logger.exception("Intro generation failed")
        raise HTTPException(status_code=500, detail=str(e))
