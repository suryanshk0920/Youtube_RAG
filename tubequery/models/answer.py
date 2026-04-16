"""
Answer Model
=============
Structured response from the LLM, including the generated text
and a list of citations pointing back to specific video moments.
"""

from dataclasses import dataclass, field


@dataclass
class Citation:
    """A reference to a specific moment in a YouTube video."""

    video_title: str       # Human-readable video title
    video_id: str          # YouTube video ID
    timestamp_label: str   # e.g. '12:34'
    youtube_url: str       # Deep link with ?t= parameter
    excerpt: str           # Short snippet from the chunk


@dataclass
class Answer:
    """Complete response from the retrieval pipeline."""

    text: str                                          # The LLM-generated answer
    citations: list[Citation]                          # Sources used
    found_relevant_content: bool = True                # False if no good chunks found
    raw_chunks: list = field(default_factory=list)     # For debugging
