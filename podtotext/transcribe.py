"""Transcription module: Whisper model loading and audio transcription."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import whisper


def load_model(model_size: str = "base") -> whisper.Whisper:
    """Load a Whisper model of the given *model_size*.

    Supported sizes: ``tiny``, ``base``, ``small``, ``medium``, ``large``.
    """
    return whisper.load_model(model_size)


def transcribe(model: whisper.Whisper, audio_path: Path) -> dict[str, Any]:
    """Transcribe *audio_path* with the preloaded Whisper *model*.

    Returns a dict with:
      - transcript: full transcription text
      - segments: list of ``{start, end, text}`` dicts
    """
    result = model.transcribe(str(audio_path))

    segments = [
        {
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
        }
        for seg in result.get("segments", [])
    ]

    return {
        "transcript": result.get("text", "").strip(),
        "segments": segments,
    }
