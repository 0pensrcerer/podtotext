"""Output module: build and save per-episode JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from podtotext.utils import slugify


def build_episode_json(
    episode: dict[str, Any],
    audio_file: Path,
    transcription: dict[str, Any],
) -> dict[str, Any]:
    """Build the final JSON structure for a single episode."""
    return {
        "title": episode.get("title", "Untitled"),
        "date": episode.get("date", ""),
        "source_url": episode.get("audio_url", ""),
        "audio_file": str(audio_file),
        "transcript": transcription["transcript"],
        "segments": transcription["segments"],
    }


def save_episode_json(
    data: dict[str, Any],
    output_dir: Path,
) -> Path:
    """Save *data* as a JSON file in *output_dir* and return the file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(data.get("title", "episode")) or "episode"
    out_path = output_dir / f"{slug}.json"

    # Avoid overwriting existing files.
    counter = 1
    while out_path.exists():
        out_path = output_dir / f"{slug}-{counter}.json"
        counter += 1

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return out_path
