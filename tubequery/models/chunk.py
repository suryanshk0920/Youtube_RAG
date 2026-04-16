"""
Chunk Model
===========
Represents a segment of video transcript with timing metadata.
Every function in the codebase passes Chunk objects — no raw dicts.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    """A single chunk of transcript text with associated metadata."""

    text: str              # The transcript text for this chunk
    video_id: str          # YouTube video ID (e.g. 'dQw4w9WgXcQ')
    video_title: str       # Human-readable video title
    start_time: float      # Start time in seconds
    end_time: float        # End time in seconds
    chunk_index: int       # Index of this chunk within the video
    source_id: str         # ID of the knowledge base source

    @property
    def youtube_url(self) -> str:
        """Deep link to the exact moment in the video."""
        t = int(self.start_time)
        return f"https://youtu.be/{self.video_id}?t={t}"

    @property
    def timestamp_label(self) -> str:
        """Human-readable timestamp (e.g. '12:34')."""
        mins = int(self.start_time // 60)
        secs = int(self.start_time % 60)
        return f"{mins}:{secs:02d}"

    def to_metadata(self) -> dict:
        """Serialize metadata for storage in the vector store."""
        return {
            "video_id": self.video_id,
            "video_title": self.video_title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "chunk_index": self.chunk_index,
            "source_id": self.source_id,
        }
