"""
YouTube Utilities
=================
Handles all YouTube URL parsing and transcript fetching.
Supports single videos, playlists, and channel URLs.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse, parse_qs

import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
)

import config

logger = logging.getLogger(__name__)

# ── URL Validation & Parsing ────────────────────────────────────────

# Allowed YouTube domains (no shortened URLs or redirects)
ALLOWED_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
}

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


def validate_youtube_url(url: str) -> None:
    """
    Validate that the URL is a legitimate YouTube URL.
    
    Raises
    ------
    ValueError
        If URL is not from an allowed YouTube domain or uses URL shorteners.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove 'www.' prefix for comparison
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check if domain is allowed
        if domain not in ALLOWED_DOMAINS and f"www.{domain}" not in ALLOWED_DOMAINS:
            raise ValueError(
                "Please use a direct YouTube link. Shortened URLs aren't supported."
            )
        
        # Ensure HTTPS
        if parsed.scheme != "https":
            raise ValueError("Please use a secure YouTube link (starting with https://)")
            
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError("That doesn't look like a valid link. Copy it directly from YouTube!")


def parse_url(url: str) -> dict:
    """
    Parse a YouTube URL and return its type and ID.
    
    Security: Only accepts direct YouTube URLs, no shortened URLs or redirects.

    Returns
    -------
    dict
        ``{'type': 'video'|'playlist'|'channel', 'id': str, 'url': str}``

    Raises
    ------
    ValueError
        If *url* is not a recognised YouTube URL or uses URL shorteners.
    """
    url = url.strip()
    
    # First, validate the URL is from YouTube
    validate_youtube_url(url)

    # Check for playlist first (higher priority than single video)
    # This catches both direct playlist URLs and video URLs with playlist parameter
    match = _PLAYLIST_PATTERN.search(url)
    if match:
        return {"type": "playlist", "id": match.group(1), "url": url}

    # Single video (only if no playlist parameter)
    match = _VIDEO_PATTERN.search(url)
    if match:
        return {"type": "video", "id": match.group(1), "url": url}

    # Channel
    for pattern in _CHANNEL_PATTERNS:
        match = pattern.search(url)
        if match:
            return {"type": "channel", "id": match.group(1), "url": url}

    raise ValueError(
        "Hmm, we couldn't recognize that YouTube link. "
        "Try copying it directly from YouTube!"
    )


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
    import os, requests, http.cookiejar

    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        # Load cookies from file if present — helps bypass IP blocks
        cookies_path = os.path.join(
            os.path.dirname(__file__), "..", "youtube_cookies.txt"
        )
        if os.path.exists(cookies_path):
            try:
                jar = http.cookiejar.MozillaCookieJar(cookies_path)
                jar.load(ignore_discard=True, ignore_expires=True)
                session.cookies.update(jar)
                logger.info("Using YouTube cookies from %s", cookies_path)
            except Exception as e:
                logger.warning("Failed to load cookies from %s: %s", cookies_path, e)
        else:
            logger.debug("No cookies file found at %s, proceeding without cookies", cookies_path)

        api = YouTubeTranscriptApi(http_client=session)
        transcript = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
        return [{"text": s.text, "start": s.start, "duration": s.duration} for s in transcript]

    except (TranscriptsDisabled, NoTranscriptFound):
        logger.warning("No transcript available for video %s", video_id)
        return []
    except Exception as exc:
        logger.warning("Could not fetch transcript for %s: %s", video_id, exc)
        return []
