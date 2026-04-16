"""
Chunker
=======
Splits a transcript (list of timed segments) into overlapping chunks
while preserving timestamp metadata for each chunk.

Strategy: accumulate segments until we reach CHUNK_SIZE words, then
start a new chunk with CHUNK_OVERLAP words of overlap. This preserves
natural sentence boundaries better than character splitting.
"""

from __future__ import annotations

import config
from models.chunk import Chunk


def chunk_transcript(
    transcript: list[dict],
    video_id: str,
    video_title: str,
    source_id: str,
) -> list[Chunk]:
    """
    Split a transcript into overlapping chunks with timestamp metadata.

    Parameters
    ----------
    transcript : list[dict]
        Each segment: ``{'text': str, 'start': float, 'duration': float}``
    video_id : str
        YouTube video ID.
    video_title : str
        Human-readable video title.
    source_id : str
        ID of the knowledge base source.

    Returns
    -------
    list[Chunk]
        Ordered list of chunks with timing metadata.
    """
    if not transcript:
        return []

    chunks: list[Chunk] = []
    current_segments: list[dict] = []
    current_word_count = 0
    chunk_index = 0

    for segment in transcript:
        words = segment["text"].split()
        current_segments.append(segment)
        current_word_count += len(words)

        if current_word_count >= config.CHUNK_SIZE:
            # Build chunk text
            chunk_text = " ".join(s["text"] for s in current_segments)
            chunk_text = chunk_text.replace("\n", " ").strip()

            chunks.append(
                Chunk(
                    text=chunk_text,
                    video_id=video_id,
                    video_title=video_title,
                    start_time=current_segments[0]["start"],
                    end_time=(
                        current_segments[-1]["start"]
                        + current_segments[-1]["duration"]
                    ),
                    chunk_index=chunk_index,
                    source_id=source_id,
                )
            )
            chunk_index += 1

            # Overlap: keep last CHUNK_OVERLAP words worth of segments
            overlap_words = 0
            overlap_segments: list[dict] = []
            for seg in reversed(current_segments):
                seg_words = len(seg["text"].split())
                if overlap_words + seg_words <= config.CHUNK_OVERLAP:
                    overlap_segments.insert(0, seg)
                    overlap_words += seg_words
                else:
                    break

            current_segments = overlap_segments
            current_word_count = overlap_words

    # Don't forget the last partial chunk (skip very short trailing chunks)
    if current_segments:
        chunk_text = " ".join(s["text"] for s in current_segments).strip()
        if len(chunk_text.split()) > 20:
            chunks.append(
                Chunk(
                    text=chunk_text,
                    video_id=video_id,
                    video_title=video_title,
                    start_time=current_segments[0]["start"],
                    end_time=(
                        current_segments[-1]["start"]
                        + current_segments[-1]["duration"]
                    ),
                    chunk_index=chunk_index,
                    source_id=source_id,
                )
            )

    return chunks
