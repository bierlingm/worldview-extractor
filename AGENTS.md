# Worldview Extractor — Agent Instructions

## Overview

`wve` (Worldview Extractor) synthesizes a person's intellectual worldview from their public video appearances. v0.2 introduces identity-first discovery and quote-grounded synthesis.

## v0.2 Workflow (Recommended)

```bash
# 1. Create identity for the person
wve identity create "Skinner Layne" --channel "https://youtube.com/@exikiex"

# 2. Option A: If they have their own channel (most reliable)
wve from-channel "https://youtube.com/@exikiex" -o transcripts/

# 2. Option B: Discover and confirm videos
wve discover "Skinner Layne" -o candidates.json
wve confirm candidates.json --accept-likely -o confirmed.json
wve fetch confirmed.json -o transcripts/

# 3. Extract quotes and generate report
wve quotes transcripts/ -o quotes.json
wve themes transcripts/ -o themes.json
wve contrast transcripts/ -s "Skinner Layne" -o contrast.json
wve report transcripts/ -s "Skinner Layne" -o report.md
```

## Quick Reference (Human)

```bash
# Identity management
wve identity create "Name" --channel URL --alias "Nick"
wve identity list
wve identity show slug
wve identity add-video slug VIDEO_ID
wve identity add-channel slug URL

# Discovery (v0.2 - search without downloading)
wve discover "Name" --max-results 20 -o candidates.json
wve confirm candidates.json --accept 1,2,3 --reject 4,5
wve fetch confirmed.json -o transcripts/

# Source commands (bypass search)
wve from-channel "https://youtube.com/@channel" -o transcripts/
wve from-urls urls.txt -o transcripts/

# Analysis (v0.2 - quote-grounded)
wve quotes transcripts/ --contrarian -o quotes.json
wve themes transcripts/ -s "Name" -o themes.json
wve contrast transcripts/ -s "Name" -o contrast.json
wve report transcripts/ -s "Name" -o report.md

# Legacy pipeline (v0.1)
wve pipeline "Name" --depth medium
wve dump transcripts/ --format markdown
wve ask transcripts/ "What's their view on X?"
```

## Quick Reference (Automation / AI)

All v0.2 commands support `--json` for machine-readable output:

```bash
wve discover "Name" --json                   # Candidates with classification
wve confirm candidates.json --accept-likely --json  # Batch confirm
wve fetch --identity slug --json             # Download status
wve quotes transcripts/ --json               # Extracted quotes
wve report transcripts/ -s "Name" --json     # Structured report
```

Status messages go to stderr when `--json` is set, output goes to stdout.

## Depth Levels

| Level | LLM Required | Time | Output Quality |
|-------|--------------|------|----------------|
| `quick` | No | ~30s | Keywords + basic themes |
| `medium` | No | ~2min | Clustered themes + evidence |
| `deep` | Ollama | ~5min | Distinctive/contrarian worldview points |

## v0.2 Commands

### `wve dump` - Concatenate transcripts for LLM input
```bash
wve dump transcripts/ -o corpus.md           # Save to file
wve dump transcripts/ --max-tokens 100000    # Warn if too large
wve dump transcripts/ --format plain         # No markdown headers
```

### `wve ask` - RAG-style corpus interrogation
```bash
wve ask transcripts/ "What does X think about Y?"
wve ask transcripts/ "Question" --top-k 10   # More context chunks
wve ask transcripts/ "Question" --show-sources  # Show retrieved chunks
```

### `--strict` flag for search
Filters results to only videos where the full query appears in the title (case-insensitive).
```bash
wve search "Skinner Layne" --strict  # Excludes "Lynyrd Skynyrd" matches
```

## Development

```bash
# Setup
cd /Users/moritzbierling/werk/tools/worldview-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ollama]"

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
- `ollama` with `mistral` model (for deep synthesis and ask)

Python dependencies managed via pyproject.toml.

## Installation (External)

```bash
pip install worldview-extractor           # From PyPI (when published)
pip install "worldview-extractor[ollama]" # With Ollama support
```

Or from source:
```bash
pip install git+https://github.com/bierlingm/worldview-extractor.git
```

## Issue Tracking

Use `bd` for all issues related to this project.
