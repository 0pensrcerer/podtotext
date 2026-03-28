"""CLI entry point for podtotext."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from podtotext.ingest import (
    detect_source_type,
    download_episode,
    is_processed,
    mark_processed,
    parse_rss,
    parse_youtube,
)
from podtotext.output import build_episode_json, save_episode_json
from podtotext.transcribe import load_model, transcribe


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="podtotext",
        description="Download podcasts and transcribe them to JSON.",
    )
    parser.add_argument(
        "url",
        help="RSS feed URL or YouTube channel/playlist URL.",
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base).",
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory for JSON output files (default: ./output).",
    )
    parser.add_argument(
        "--staging-dir",
        default="./staging",
        help="Directory for downloaded audio files (default: ./staging).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the podtotext pipeline."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    staging_dir = Path(args.staging_dir)
    state_file = staging_dir / "processed.json"

    # --- Detect source type and fetch episode list -------------------------
    source_type = detect_source_type(args.url)
    print(f"Detected source type: {source_type}")

    if source_type == "youtube":
        episodes = parse_youtube(args.url)
    else:
        episodes = parse_rss(args.url)

    if not episodes:
        print("No episodes found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(episodes)} episode(s).")

    # --- Load Whisper model once -------------------------------------------
    print(f"Loading Whisper model '{args.model}'...")
    model = load_model(args.model)

    # --- Process each episode sequentially ---------------------------------
    for i, episode in enumerate(episodes, start=1):
        title = episode.get("title", "Untitled")
        print(f"\n[{i}/{len(episodes)}] {title}")

        # Skip if already fully processed
        if is_processed(episode, state_file):
            print("  Skipped (already processed).")
            continue

        # Download
        audio_path = download_episode(episode, staging_dir)
        print(f"  Downloaded: {audio_path}")

        # Transcribe
        print("  Transcribing...")
        transcription = transcribe(model, audio_path)
        print(f"  Transcript length: {len(transcription['transcript'])} chars")

        # Output
        data = build_episode_json(episode, audio_path, transcription)
        json_path = save_episode_json(data, output_dir)
        print(f"  Saved: {json_path}")

        # Mark as fully processed only after the entire pipeline succeeds
        mark_processed(episode, state_file)

    print("\nDone.")
