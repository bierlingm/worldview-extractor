# Worldview Extractor

Synthesize a person's intellectual worldview from their public video appearances.

## Installation

```bash
pip install worldview-extractor
```

Or from source:

```bash
git clone https://github.com/bierlingm/worldview-extractor
cd worldview-extractor
pip install -e .
```

**External dependencies:**
```bash
brew install yt-dlp  # Required
brew install ollama  # Optional, for deep synthesis
```

## Quick Start

```bash
# Full pipeline: search → transcripts → extract → cluster → synthesize
wve pipeline "EM Burlingame" --depth medium --max-videos 10

# Output: worldview.json + worldview.md
```

## Usage

### Step-by-step

```bash
# 1. Find videos
wve search "Person Name" --max-results 10 -o videos.json

# 2. Download transcripts
wve transcripts videos.json -o transcripts/

# 3. Extract themes
wve extract transcripts/ -o extraction.json

# 4. Cluster concepts
wve cluster extraction.json -o clusters.json

# 5. Synthesize worldview
wve synthesize clusters.json --depth medium -o worldview.json
```

### Depth Levels

- **quick**: Keyword extraction only (no LLM, instant)
- **medium**: Clustering + evidence gathering (no LLM, ~2 min)
- **deep**: Full Ollama synthesis (~5 min, requires local Ollama)

## Output Example

```json
{
  "subject": "EM Burlingame",
  "points": [
    {
      "point": "Civilizations vs Nation-States",
      "elaboration": "Nation-states are atomized constructs...",
      "confidence": 0.85,
      "evidence": ["civilization", "nation-state", "Westphalian"],
      "sources": ["video1.txt:L123"]
    }
  ],
  "depth": "medium"
}
```

## Configuration

`~/.config/wve/config.toml`:

```toml
[search]
default_max_results = 10

[synthesize]
default_depth = "medium"
ollama_model = "llama3"
```

## License

MIT
