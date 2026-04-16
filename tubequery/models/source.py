"""
Source Model
============
Tracks metadata about ingested content (a video, playlist, or channel).
Used for UI display and persistence — vector data lives in ChromaDB.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SourceType(Enum):
    """The kind of YouTube content that was ingested."""
    VIDEO = "video"
    PLAYLIST = "playlist"
    CHANNEL = "channel"


class IngestionStatus(Enum):
    """Current state of the ingestion pipeline for this source."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Source:
    """Metadata record for an ingested YouTube source."""

    id: str                          # Unique ID for this source
    url: str                         # Original URL the user pasted
    source_type: SourceType          # video / playlist / channel
    title: str                       # Display name
    kb_id: str                       # Which knowledge base this belongs to
    status: IngestionStatus = IngestionStatus.PENDING
    video_count: int = 0             # How many videos were ingested
    chunk_count: int = 0             # How many chunks were stored
    error_message: str = ""          # If failed, why
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
