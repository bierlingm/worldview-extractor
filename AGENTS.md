# Worldview Extractor — Agent Instructions

## Overview

`wve` (Worldview Extractor) synthesizes a person's intellectual worldview from their public video appearances. It prioritizes local computation over paid inference.

## Quick Reference

```bash
# Full pipeline
wve pipeline "Person Name" --depth medium --max-videos 10

# Step by step
wve search "Person Name" --max-results 10 -o videos.json
wve transcripts videos.json -o transcripts/
wve extract transcripts/ -o extraction.json
wve cluster extraction.json -o clusters.json
wve synthesize clusters.json --depth medium -o worldview.json

# Inspect any artifact
wve inspect worldview.json
```

## Depth Levels

| Level | LLM Required | Time | Output Quality |
|-------|--------------|------|----------------|
| `quick` | No | ~30s | Keywords + basic themes |
| `medium` | No | ~2min | Clustered themes + evidence |
| `deep` | Ollama | ~5min | Full synthesis with elaboration |

## Development

```bash
# Setup
cd /Users/moritzbierling/werk/tools/worldview-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run specific test category
pytest tests/ -v -m "not slow"  # Skip slow tests
pytest tests/ -v -m "robustness"  # Noise/edge case tests
```

## Architecture

See `SPECIFICATION.md` for full details. Key points:

1. **Compute hierarchy:** Code → Local NLP → Local embeddings → Ollama → Droid
2. **Artifacts:** Each stage produces JSON artifacts that can be inspected/resumed
3. **Caching:** All artifacts cached by content hash in `~/.cache/wve/`

## Dependencies

Required external tools:
- `yt-dlp` (brew install yt-dlp)
- `ollama` (for deep synthesis only)

Python dependencies managed via pyproject.toml.

## Issue Tracking

Use `bd` for all issues related to this project.
