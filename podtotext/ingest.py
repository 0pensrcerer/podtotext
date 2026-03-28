"""Ingestion module: RSS feed parsing, YouTube support, and audio download."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import feedparser
import yt_dlp

from podtotext.utils import slugify


def _load_processed(state_file: Path) -> set[str]:
    """Load the set of already-processed episode identifiers."""
    if state_file.exists():
        data = json.loads(state_file.read_text())
        return set(data)
    return set()


def _save_processed(state_file: Path, processed: set[str]) -> None:
    """Persist the set of processed episode identifiers."""
    state_file.write_text(json.dumps(sorted(processed), indent=2))


# ---------------------------------------------------------------------------
# RSS path
# ---------------------------------------------------------------------------

def parse_rss(feed_url: str) -> list[dict[str, Any]]:
    """Parse an RSS feed and return episode metadata.

    Each returned dict contains:
      - title: episode title
      - date: published date string
      - guid: unique episode identifier
      - audio_url: URL to the audio enclosure
    """
    feed = feedparser.parse(feed_url)
    episodes: list[dict[str, Any]] = []
    for entry in feed.entries:
        audio_url: str | None = None
        for link in getattr(entry, "enclosures", []):
            if "audio" in link.get("type", ""):
                audio_url = link.get("href")
                break
        # Fallback: first enclosure regardless of type
        if audio_url is None:
            for link in getattr(entry, "enclosures", []):
                audio_url = link.get("href")
                break

        if audio_url is None:
            continue

        episodes.append(
            {
                "title": entry.get("title", "Untitled"),
                "date": entry.get("published", ""),
                "guid": entry.get("id", audio_url),
                "audio_url": audio_url,
            }
        )
    return episodes


# ---------------------------------------------------------------------------
# YouTube path
# ---------------------------------------------------------------------------

def parse_youtube(url: str) -> list[dict[str, Any]]:
    """Extract episode metadata from a YouTube channel/playlist URL.

    Uses yt-dlp to enumerate videos without downloading them.
    """
    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": False,
    }
    episodes: list[dict[str, Any]] = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get("entries") or [info]
        for entry in entries:
            video_url = entry.get("url") or entry.get("webpage_url", url)
            episodes.append(
                {
                    "title": entry.get("title", "Untitled"),
                    "date": entry.get("upload_date", ""),
                    "guid": entry.get("id", video_url),
                    "audio_url": video_url,
                }
            )
    return episodes


# ---------------------------------------------------------------------------
# Shared download
# ---------------------------------------------------------------------------

def download_episode(
    episode: dict[str, Any],
    staging_dir: Path,
    state_file: Path,
) -> Path | None:
    """Download a single episode's audio as WAV to *staging_dir*.

    Returns the path to the downloaded WAV file, or ``None`` if the episode
    was already processed.
    """
    processed = _load_processed(state_file)
    guid = episode["guid"]
    if guid in processed:
        return None

    slug = slugify(episode["title"]) or "episode"
    out_path = staging_dir / f"{slug}.wav"

    # Avoid filename collisions by appending a counter.
    counter = 1
    while out_path.exists():
        out_path = staging_dir / f"{slug}-{counter}.wav"
        counter += 1

    os.makedirs(staging_dir, exist_ok=True)

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": str(out_path.with_suffix(".%(ext)s")),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([episode["audio_url"]])

    # Mark as processed
    processed.add(guid)
    _save_processed(state_file, processed)

    return out_path


# ---------------------------------------------------------------------------
# Source-type detection
# ---------------------------------------------------------------------------

def detect_source_type(url: str) -> str:
    """Return ``'youtube'`` or ``'rss'`` based on the URL."""
    yt_patterns = ["youtube.com", "youtu.be", "youtube.googleapis.com"]
    if any(p in url for p in yt_patterns):
        return "youtube"
    return "rss"
