"""
Sources Router
==============
GET    /sources          — list all sources (optionally filter by kb_id)
DELETE /sources/{id}     — remove a source and its vectors
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_vector_store
from api.schemas import SourceOut
from core.source_store import delete_source_record, load_sources

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(kb_id: str | None = Query(None, description="Filter by knowledge base")):
    """List all ingested sources, optionally filtered by kb_id."""
    sources = load_sources(kb_id=kb_id)
    return [
        SourceOut(
            id=s.id,
            title=s.title,
            url=s.url,
            source_type=s.source_type.value,
            kb_id=s.kb_id,
            status=s.status.value,
            video_count=s.video_count,
            chunk_count=s.chunk_count,
            created_at=s.created_at,
        )
        for s in sources
    ]


@router.delete("/{source_id}", status_code=204)
def delete_source(
    source_id: str,
    kb_id: str = Query(..., description="Knowledge base the source belongs to"),
    vector_store=Depends(get_vector_store),
):
    """Remove a source's vectors from ChromaDB and its metadata record."""
    sources = load_sources()
    source = next((s for s in sources if s.id == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    vector_store.delete_source(source_id, kb_id)
    delete_source_record(source_id)
