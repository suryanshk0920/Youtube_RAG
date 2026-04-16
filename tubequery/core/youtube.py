"""
YouTube Utilities
=================
Handles all YouTube URL parsing and transcript fetching.
Supports single videos, playlists, and channel URLs.
"""

from __future__ import annotations

import logging
import re

import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
)

import config

logger = logging.getLogger(__name__)

# ── URL Parsing ─────────────────────────────────────────────────────

# Pre-compiled patterns for efficiency
_VIDEO_PATTERN = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
)
_PLAYLIST_PATTERN = re.compile(r"[?&]list=([a-zA-Z0-9_-]+)")
_CHANNEL_PATTERNS = [
    re.compile(r"youtube\.com/@([a-zA-Z0-9_-]+)"),
    re.compile(r"youtube\.com/channel/([a-zA-Z0-9_-]+)"),
    re.compile(r"youtube\.com/c/([a-zA-Z0-9_-]+)"),
]


def parse_url(url: str) -> dict:
    """
    Parse a YouTube URL and return its type and ID.

    Returns
    -------
    dict
        ``{'type': 'video'|'playlist'|'channel', 'id': str, 'url': str}``

    Raises
    ------
    ValueError
        If *url* is not a recognised YouTube URL.
    """
    url = url.strip()

    # Single video
    match = _VIDEO_PATTERN.search(url)
    if match:
        return {"type": "video", "id": match.group(1), "url": url}

    # Playlist
    match = _PLAYLIST_PATTERN.search(url)
    if match:
        return {"type": "playlist", "id": match.group(1), "url": url}

    # Channel
    for pattern in _CHANNEL_PATTERNS:
        match = pattern.search(url)
        if match:
            return {"type": "channel", "id": match.group(1), "url": url}

    raise ValueError(f"Could not parse YouTube URL: {url}")


# ── Playlist Video Enumeration ──────────────────────────────────────

def get_video_ids_from_playlist(playlist_id: str) -> list[dict]:
    """
    Fetch all video IDs from a playlist using YouTube Data API v3.

    Returns
    -------
    list[dict]
        Each dict has ``{'video_id': str, 'title': str}``.
        Deleted and private videos are filtered out.
    """
    if not config.YOUTUBE_API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY is not set. "
            "Add it to your .env file to use playlist ingestion."
        )

    videos: list[dict] = []
    next_page_token: str | None = None
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"

    while True:
        params: dict = {
            "part": "contentDetails,snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": config.YOUTUBE_API_KEY,
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        response = httpx.get(base_url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            vid_id = item["contentDetails"]["videoId"]
            title = item["snippet"]["title"]
            if title not in ("Deleted video", "Private video"):
                videos.append({"video_id": vid_id, "title": title})

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    logger.info("Found %d videos in playlist %s", len(videos), playlist_id)
    return videos


# ── Video Title Fetching ────────────────────────────────────────────

def get_video_title(video_id: str) -> str:
    """
    Fetch the title of a YouTube video using the oEmbed API.
    No API key required.

    Returns the video ID as fallback if the request fails.
    """
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json().get("title", video_id)
    except Exception as exc:
        logger.warning("Could not fetch title for %s: %s", video_id, exc)
        return video_id


# ── Transcript Fetching ─────────────────────────────────────────────

def fetch_transcript(video_id: str) -> list[dict]:
    """
    Fetch transcript for a single video.

    Returns
    -------
    list[dict]
        Each dict has ``{'text': str, 'start': float, 'duration': float}``.
        Returns an empty list if the transcript is unavailable.
    """
    try:
        # v1.x API: instantiate first, then call fetch
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
        # v1.x returns a FetchedTranscript object — convert to list of dicts
        return [{"text": s.text, "start": s.start, "duration": s.duration} for s in transcript]
    except (TranscriptsDisabled, NoTranscriptFound):
        logger.warning("No transcript available for video %s", video_id)
        return []
    except Exception as exc:
        logger.warning(
            "Could not fetch transcript for %s: %s", video_id, exc
        )
        return []
