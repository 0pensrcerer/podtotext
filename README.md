# podtotext

A Python CLI tool that downloads podcast and video audio, transcribes it locally with [Whisper](https://github.com/openai/whisper), and saves per-episode JSON files with metadata and timestamped segments.

## How it works

1. **Ingest** — Parses an RSS feed or YouTube channel/playlist URL and collects episode metadata
2. **Download** — Fetches each episode's audio as WAV via [yt-dlp](https://github.com/yt-dlp/yt-dlp)
3. **Transcribe** — Runs audio through a local Whisper model
4. **Output** — Writes a JSON file per episode with the full transcript and per-segment timestamps

Re-runs are safe: processed episodes are tracked in `staging/processed.json` and skipped automatically.

## Prerequisites

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/) (required by yt-dlp for audio extraction)
- A CUDA-capable GPU is optional but significantly speeds up transcription

## Installation

```bash
git clone https://github.com/0pensrcerer/podtotext.git
cd podtotext
pip install -r requirements.txt
```

## Usage

```
python -m podtotext <URL> [options]
```

| Argument | Default | Description |
|---|---|---|
| `url` | *(required)* | RSS feed URL or YouTube channel/playlist URL |
| `--model` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| `--output-dir` | `./output` | Directory for JSON transcript files |
| `--staging-dir` | `./staging` | Directory for downloaded audio files |

### Examples

```bash
# Transcribe a podcast RSS feed with the default model
python -m podtotext "https://example.com/podcast/feed.xml"

# Transcribe a YouTube playlist with a faster, smaller model
python -m podtotext "https://www.youtube.com/playlist?list=PLxxxx" --model tiny

# Use a higher-quality model and custom output paths
python -m podtotext "https://example.com/feed.xml" \
  --model small \
  --output-dir ./transcripts \
  --staging-dir ./audio
```

## Output format

Each episode produces a JSON file at `<output-dir>/<episode-slug>.json`:

```json
{
  "title": "Episode Title",
  "date": "Mon, 01 Jan 2024 00:00:00 +0000",
  "source_url": "https://example.com/audio.mp3",
  "audio_file": "staging/episode-title.wav",
  "transcript": "Full transcription text...",
  "segments": [
    { "start": 0.0,  "end": 3.5,  "text": "Welcome to the show." },
    { "start": 3.5,  "end": 7.2,  "text": "Today we're talking about..." }
  ]
}
```

Downloaded audio files are kept in `staging/` so you can re-transcribe with a better model later without re-downloading.

## Model size guide

| Model | Parameters | Relative speed | Relative accuracy |
|---|---|---|---|
| `tiny` | 39 M | Fastest | Lowest |
| `base` | 74 M | Fast | Good |
| `small` | 244 M | Moderate | Better |
| `medium` | 769 M | Slow | High |
| `large` | 1550 M | Slowest | Highest |

## Project structure

```
podtotext/
├── podtotext/
│   ├── __init__.py      # Package marker
│   ├── __main__.py      # python -m podtotext entry point
│   ├── cli.py           # Argument parsing and pipeline orchestration
│   ├── ingest.py        # RSS/YouTube parsing and audio download
│   ├── transcribe.py    # Whisper model loading and transcription
│   ├── output.py        # JSON building and saving
│   └── utils.py         # Shared helpers (slugify)
└── requirements.txt
```

## License

MIT
