"""
Ingestion Pipeline
==================
Orchestrates the full ingestion flow:
    URL → parse → get videos → fetch transcripts → chunk → embed → store

This is the function the UI calls. Supports a progress callback
so the Streamlit progress bar can display real-time updates.
"""

from __future__ import annotations

import logging
import uuid

from core.chunker import chunk_transcript
from core.youtube import (
    fetch_transcript,
    get_video_ids_from_playlist,
    get_video_title,
    parse_url,
)
from models.source import IngestionStatus, Source, SourceType
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Type alias for the progress callback
ProgressCallback = callable  # fn(current: int, total: int, message: str)


def ingest_url(
    url: str,
    kb_id: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    progress_callback: ProgressCallback | None = None,
) -> Source:
    """
    Full ingestion pipeline.

    Parameters
    ----------
    url : str
        YouTube video, playlist, or channel URL.
    kb_id : str
        Knowledge base ID to store chunks in.
    embedding_service : EmbeddingService
        Service to generate embeddings.
    vector_store : VectorStore
        Store for persisting embedded chunks.
    progress_callback : callable, optional
        Called with ``(current, total, message)`` for progress reporting.

    Returns
    -------
    Source
        Completed source object with final stats.

    Raises
    ------
    ValueError
        If the URL cannot be parsed.
    NotImplementedError
        If channel ingestion is attempted (use playlist URL instead).
    """
    parsed = parse_url(url)
    source_id = str(uuid.uuid4())[:8]

    source = Source(
        id=source_id,
        url=url,
        source_type=SourceType(parsed["type"]),
        title=parsed["id"],  # Updated with real title when available
        kb_id=kb_id,
        status=IngestionStatus.PROCESSING,
    )

    # ── Gather video list ───────────────────────────────────────────
    if parsed["type"] == "video":
        real_title = get_video_title(parsed["id"])
        videos = [{"video_id": parsed["id"], "title": real_title}]
        source.title = real_title
    elif parsed["type"] == "playlist":
        videos = get_video_ids_from_playlist(parsed["id"])
        source.title = f"Playlist: {parsed['id']}"
    else:
        raise NotImplementedError(
            "Channel ingestion is not yet supported. "
            "Please use a playlist URL instead."
        )

    total = len(videos)
    total_chunks = 0
    processed_videos = 0

    logger.info(
        "Starting ingestion of %d video(s) into KB '%s'", total, kb_id
    )

    # ── Process each video ──────────────────────────────────────────
    for i, video in enumerate(videos):
        vid_id = video["video_id"]
        vid_title = video["title"]

        if progress_callback:
            progress_callback(i, total, f"Processing: {vid_title}")

        # Fetch transcript
        transcript = fetch_transcript(vid_id)
        if not transcript:
            logger.warning("Skipping %s (no transcript)", vid_id)
            continue

        logger.info(
            "Fetched %d transcript segments for %s (total duration: %.1f min)",
            len(transcript),
            vid_id,
            transcript[-1]["start"] / 60 if transcript else 0,
        )

        # Chunk transcript
        chunks = chunk_transcript(
            transcript=transcript,
            video_id=vid_id,
            video_title=vid_title,
            source_id=source_id,
        )
        if not chunks:
            continue

        # Embed and store in batches
        batch_size = 64
        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start : batch_start + batch_size]
            embeddings = embedding_service.embed([c.text for c in batch])
            vector_store.upsert(batch, embeddings, kb_id)
            total_chunks += len(batch)

        processed_videos += 1

    # ── Finalise ────────────────────────────────────────────────────
    source.video_count = processed_videos
    source.chunk_count = total_chunks
    source.status = IngestionStatus.COMPLETE

    if progress_callback:
        progress_callback(total, total, "Complete!")

    logger.info(
        "Ingestion complete: %d videos, %d chunks",
        processed_videos,
        total_chunks,
    )
    return source
