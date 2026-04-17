"""
Ingest Router
=============
POST /ingest                    — ingest a YouTube URL (blocking)
GET  /ingest/progress/{job_id}  — SSE stream of ingestion progress
GET  /ingest/{source_id}/intro  — generate summary + suggested questions
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import get_embedding_service, get_llm_service, get_vector_store
from api.schemas import IngestRequest, IngestResponse, IntroResponse
from core.ingestion import ingest_url
from core.retriever import generate_intro
from core.source_store import load_sources, save_source

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


# ── Streaming ingestion ──────────────────────────────────────────────

@router.post("/stream")
def ingest_stream(
    body: IngestRequest,
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
):
    """
    Ingest a URL and stream progress via SSE.

    Event types:
      data: {"type": "step",     "step": "...", "detail": "..."}
      data: {"type": "progress", "current": int, "total": int, "video": "..."}
      data: {"type": "done",     "source": {...}}
      data: {"type": "error",    "detail": "..."}
    """
    # Deduplication check
    existing = load_sources(kb_id=body.kb_id)
    duplicate = next(
        (s for s in existing if s.url.strip() == body.url.strip() and s.chunk_count > 0),
        None,
    )
    if duplicate:
        def already_done():
            yield f"data: {json.dumps({'type': 'step', 'step': 'cached', 'detail': 'Already ingested'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'source': {'source_id': duplicate.id, 'title': duplicate.title, 'kb_id': duplicate.kb_id, 'video_count': duplicate.video_count, 'chunk_count': duplicate.chunk_count, 'status': duplicate.status.value}})}\n\n"
        return StreamingResponse(already_done(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    def event_stream() -> Generator[str, None, None]:
        try:
            steps = []

            def progress_callback(current: int, total: int, message: str) -> None:
                event = json.dumps({"type": "progress", "current": current, "total": total, "video": message})
                steps.append(f"data: {event}\n\n")

            # Step 1
            yield f"data: {json.dumps({'type': 'step', 'step': 'fetch', 'detail': 'Fetching transcript…'})}\n\n"

            source = ingest_url(
                url=body.url,
                kb_id=body.kb_id,
                embedding_service=embedding_service,
                vector_store=vector_store,
                progress_callback=progress_callback,
            )

            # Flush buffered progress events
            for s in steps:
                yield s

            if source.chunk_count == 0:
                yield f"data: {json.dumps({'type': 'error', 'detail': 'No transcript available for this video. Captions may be disabled.'})}\n\n"
                return

            save_source(source)

            yield f"data: {json.dumps({'type': 'step', 'step': 'done', 'detail': f'{source.chunk_count} chunks indexed'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'source': {'source_id': source.id, 'title': source.title, 'kb_id': source.kb_id, 'video_count': source.video_count, 'chunk_count': source.chunk_count, 'status': source.status.value}})}\n\n"

        except Exception as e:
            logger.exception("Streaming ingestion failed")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Blocking ingestion (kept for compatibility) ──────────────────────


@router.post("", response_model=IngestResponse)
def ingest(
    body: IngestRequest,
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
):
    """
    Ingest a YouTube video or playlist URL.
    Returns source metadata including chunk count.
    Skips if the same URL is already ingested in the same KB.
    """
    # ── Deduplication check ─────────────────────────────────────────
    existing = load_sources(kb_id=body.kb_id)
    duplicate = next(
        (s for s in existing if s.url.strip() == body.url.strip() and s.chunk_count > 0),
        None,
    )
    if duplicate:
        return IngestResponse(
            source_id=duplicate.id,
            title=duplicate.title,
            kb_id=duplicate.kb_id,
            video_count=duplicate.video_count,
            chunk_count=duplicate.chunk_count,
            status=duplicate.status.value,
        )

    try:
        source = ingest_url(
            url=body.url,
            kb_id=body.kb_id,
            embedding_service=embedding_service,
            vector_store=vector_store,
        )
        save_source(source)

        if source.chunk_count == 0:
            raise HTTPException(
                status_code=422,
                detail="Ingestion completed but no chunks were stored. "
                       "The video may have no English transcript available. "
                       "Try a different video or check if captions are enabled."
            )

        return IngestResponse(
            source_id=source.id,
            title=source.title,
            kb_id=source.kb_id,
            video_count=source.video_count,
            chunk_count=source.chunk_count,
            status=source.status.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}/intro", response_model=IntroResponse)
def get_intro(
    source_id: str,
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
    llm_service=Depends(get_llm_service),
):
    """
    Generate a summary, topic list, and suggested questions for an ingested source.
    """
    sources = load_sources()
    source = next((s for s in sources if s.id == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    try:
        data = generate_intro(
            source=source,
            embedding_service=embedding_service,
            vector_store=vector_store,
            llm_service=llm_service,
        )
        return IntroResponse(
            source_id=source_id,
            intro=data.get("intro", ""),
            topics=data.get("topics", []),
            questions=data.get("questions", []),
        )
    except Exception as e:
        logger.exception("Intro generation failed")
        raise HTTPException(status_code=500, detail=str(e))
