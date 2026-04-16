"""
Source Store
============
Lightweight JSON persistence for source metadata (display info for the UI).
The actual vector data lives in ChromaDB — this only stores titles,
video counts, statuses, and other UI-facing metadata.
"""

from __future__ import annotations

import json
import logging
import os

import config
from models.source import IngestionStatus, Source, SourceType

logger = logging.getLogger(__name__)


def save_source(source: Source) -> None:
    """Append or update a source in ``sources.json``."""
    sources = _read_all()
    sources[source.id] = {
        "id": source.id,
        "url": source.url,
        "source_type": source.source_type.value,
        "title": source.title,
        "kb_id": source.kb_id,
        "status": source.status.value,
        "video_count": source.video_count,
        "chunk_count": source.chunk_count,
        "error_message": source.error_message,
        "created_at": source.created_at,
    }
    _write_all(sources)
    logger.info("Saved source %s (%s)", source.id, source.title)


def load_sources(kb_id: str | None = None) -> list[Source]:
    """
    Load all sources, optionally filtered by *kb_id*.

    Parameters
    ----------
    kb_id : str, optional
        If provided, only sources belonging to this knowledge base
        are returned.

    Returns
    -------
    list[Source]
    """
    data = _read_all()
    sources: list[Source] = []
    for item in data.values():
        source = Source(
            id=item["id"],
            url=item["url"],
            source_type=SourceType(item["source_type"]),
            title=item["title"],
            kb_id=item["kb_id"],
            status=IngestionStatus(item["status"]),
            video_count=item.get("video_count", 0),
            chunk_count=item.get("chunk_count", 0),
            error_message=item.get("error_message", ""),
            created_at=item.get("created_at", ""),
        )
        if kb_id is None or source.kb_id == kb_id:
            sources.append(source)
    return sources


def delete_source_record(source_id: str) -> None:
    """Remove a source record from ``sources.json``."""
    sources = _read_all()
    if source_id in sources:
        del sources[source_id]
        _write_all(sources)
        logger.info("Deleted source record %s", source_id)


# ── Internal helpers ────────────────────────────────────────────────

def _read_all() -> dict:
    """Read the entire sources JSON file."""
    if not os.path.exists(config.SOURCES_FILE):
        return {}
    try:
        with open(config.SOURCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read sources file: %s", exc)
        return {}


def _write_all(data: dict) -> None:
    """Write the entire sources dict to JSON."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
