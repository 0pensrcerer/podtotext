"""Shared utility functions for podtotext."""

from __future__ import annotations

import re


def slugify(text: str) -> str:
    """Return a filesystem-safe slug for *text*."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")
