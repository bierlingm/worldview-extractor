# Weave

**Synthesize intellectual worldviews from any source.** Weave transforms videos, articles, podcasts, and documents into structured belief systems with themes, quotes, and contrarian analysis.

## Installation

```bash
pip install weave
```

**Required:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video transcripts
```bash
brew install yt-dlp   # macOS
# or: pip install yt-dlp
```

**Optional:** [Ollama](https://ollama.ai) for deep LLM synthesis
```bash
brew install ollama && ollama pull llama3
```

---

## Quick Start

### One Command: URL to Worldview

```bash
# From a YouTube video
wve run https://youtube.com/watch?v=xyz -s "Person Name"

# From multiple URLs
wve run -u URL1 -u URL2 -s "Person Name"

# From a file of URLs
wve run urls.txt -s "Person Name"

# From existing transcripts
wve run ./transcripts/ -s "Person Name" --report-only
```

**Output:** `./wve-output/report.md` with themes, quotes, and contrarian views.

### Example Output

```
# Worldview: Naval Ravikant

## Themes
- **Wealth** (47x)
- **Leverage** (32x)
- **Happiness** (28x)

## Notable Quotes
1. "Seek wealth, not money or status. Wealth is having assets that earn while you sleep."
2. "Code and media are permissionless leverage. They're the leverage behind the newly rich."

## Contrarian Views
1. "Reading is faster than listening. Doing is faster than watching."
```

---

## Commands

### `wve run` — One-Shot Extraction (NEW in v0.4)

The simplest way to extract a worldview. Handles everything automatically.

```bash
wve run <input> -s "Subject Name" [options]
```

**Input types (auto-detected):**
- YouTube URLs: `https://youtube.com/watch?v=...`
- Local files: `transcript.txt`, `notes.md`
- Directories: `./transcripts/`
- URL list files: `urls.txt` (one URL per line)

**Options:**
| Flag | Description |
|------|-------------|
| `-s, --subject` | Subject name (required) |
| `-o, --output` | Output directory (default: `./wve-output`) |
| `-u, --url` | Additional URL(s) to include |
| `--lang` | Transcript language (default: `en`) |
| `--save` | Persist to store for later reference |
| `--force` | Re-download even if transcripts exist |
| `--fetch-only` | Download transcripts only, skip analysis |
| `--report-only` | Analyze existing transcripts only |
| `--json` | Output as JSON for automation |

**Examples:**
```bash
# Basic usage
wve run https://youtube.com/watch?v=abc -s "Naval Ravikant"

# Multiple sources
wve run video1.txt video2.txt -s "Naval" -o ./naval-worldview

# Resume from existing transcripts
wve run ./transcripts/ -s "Naval" --report-only

# Save to persistent store
wve run urls.txt -s "Naval Ravikant" --save

# JSON output for scripting
wve run ./transcripts/ -s "Naval" --report-only --json
```

---

### Discovery & Curation

For building larger corpora with quality control:

```bash
# Search without downloading
wve discover "Person Name" -o candidates.json

# Review and confirm candidates
wve confirm candidates.json -o confirmed.json

# Download confirmed transcripts
wve fetch confirmed.json -o transcripts/

# Generate report
wve report transcripts/ -s "Person Name"
```

### Channel Scraping

```bash
# Get all videos from a YouTube channel
wve from-channel https://youtube.com/@channel -o transcripts/ -n 50
```

### Identity Management

Track people across sources:

```bash
# Create identity profile
wve identity create "Naval Ravikant" -c https://youtube.com/@naval

# Add confirmed videos
wve identity add-video naval https://youtube.com/watch?v=...

# Fetch all confirmed content
wve fetch --identity naval -o transcripts/
```

---

## Workflows

### Simple: Single Source

```bash
wve run https://youtube.com/watch?v=xyz -s "Person"
```

### Standard: Multiple Videos

```bash
# Create URL list
cat > urls.txt << EOF
https://youtube.com/watch?v=abc
https://youtube.com/watch?v=def
https://youtube.com/watch?v=ghi
EOF

# Extract worldview
wve run urls.txt -s "Person Name" --save
```

### Advanced: Full Pipeline

```bash
# 1. Search and classify
wve discover "Person Name" -n 30 -o candidates.json

# 2. Confirm good videos
wve confirm candidates.json --accept-likely -o confirmed.json

# 3. Download transcripts
wve fetch confirmed.json -o transcripts/

# 4. Extract themes with quotes
wve themes transcripts/ -s "Person" -o themes.json

# 5. Find contrarian views
wve contrast transcripts/ -s "Person" -o contrarian.json

# 6. Generate full report
wve report transcripts/ -s "Person" -o worldview.md
```

### Automation: JSON Mode

All commands support `--json` for scripting:

```bash
# Get JSON output
wve run ./transcripts/ -s "Person" --report-only --json > result.json

# Parse with jq
wve run ./transcripts/ -s "Person" --json | jq '.themes[:5]'
```

---

## Analysis Commands

### `wve quotes`
Extract notable quotes with scoring:
```bash
wve quotes transcripts/ -n 50 --contrarian
```

### `wve themes`
Extract themes grounded in quotes:
```bash
wve themes transcripts/ -s "Person" -n 10
```

### `wve contrast`
Find contrarian/distinctive beliefs:
```bash
wve contrast transcripts/ -s "Person"
```

### `wve ask`
RAG-style Q&A over transcripts:
```bash
wve ask transcripts/ "What does Person think about X?"
```

### `wve dump`
Concatenate transcripts for LLM context:
```bash
wve dump transcripts/ --format markdown > context.md
```

---

## Persistent Store

Save worldviews for later reference:

```bash
# Save extraction
wve run urls.txt -s "Naval Ravikant" --save

# Or save existing transcripts
wve store save transcripts/ -n "Naval Ravikant" -t philosophy -t wealth

# List stored worldviews
wve store list

# Search
wve store search "naval"

# Show details
wve store show naval-ravikant
```

---

## Output Formats

### Markdown Report (`report.md`)

```markdown
# Worldview: Naval Ravikant

*Generated: 2026-01-29 10:30*

- **Sources:** 15
- **Quotes:** 87

## Themes
- **Wealth** (47x)
- **Leverage** (32x)

## Notable Quotes
1. "Seek wealth, not money..."

## Contrarian Views
1. "Reading is faster than listening..."
```

### JSON Output (`--json`)

```json
{
  "subject": "Naval Ravikant",
  "source_count": 15,
  "themes": [
    {"name": "Wealth", "count": 47},
    {"name": "Leverage", "count": 32}
  ],
  "top_quotes": [...],
  "contrarian_quotes": [...]
}
```

---

## Configuration

`~/.config/wve/config.toml`:

```toml
[search]
default_max_results = 20
min_duration = 5
max_duration = 180

[synthesis]
default_depth = "medium"
ollama_model = "llama3"

[store]
path = "~/.local/share/wve/store"
```

---

## Requirements

- Python 3.10+
- yt-dlp (for video transcripts)
- ~2GB disk space (for ML models on first run)

**Optional:**
- Ollama (for deep LLM synthesis)
- spaCy English model: `python -m spacy download en_core_web_sm`

---

## License

MIT
