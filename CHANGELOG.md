# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-01-29 "Central Library"

### Changed

**Central store is now the default** — Worldviews are automatically saved to `~/.wve/store/{slug}/` instead of the current directory. This creates a persistent library of all extracted worldviews.

- Use `-o <path>` to save locally instead
- Use `wve store list` to see your collection
- Use `wve store show <slug>` to view details

**Enhanced UX with rich output**:
- Progress bars with spinners during downloads
- Success panel showing summary stats
- Top quote previews in terminal output
- Contextual "What's next?" suggestions
- Helpful error messages with recovery tips

### Fixed

- Theme tokenization now properly strips punctuation (no more "It'S" or trailing commas)
- Expanded stopwords to filter contractions and filler words

## [0.4.0] - 2026-01-29 "One Shot"

### Added

**`wve run` — One-Shot Extraction**

The new primary entry point for Weave. Go from URL to worldview report in a single command:

```bash
wve run https://youtube.com/watch?v=xyz -s "Person Name"
```

Features:
- **Auto-detection**: Automatically classifies inputs as URLs, local files, directories, or URL list files
- **Smart resume**: Skips download if transcripts already exist (use `--force` to override)
- **Flexible input**: Mix URLs (`-u`), files, and directories in one command
- **Multiple modes**:
  - `--fetch-only`: Download transcripts without analysis
  - `--report-only`: Analyze existing transcripts without downloading
  - `--save`: Persist to store for later reference
  - `--json`: JSON output for automation/scripting

**Complete test coverage** for the run command (16 tests covering input classification, report generation, JSON output, resume logic, store integration, and edge cases).

### Changed

- README completely rewritten with comprehensive documentation
- `wve run` is now the recommended entry point (replaces `pipeline` for most use cases)
- All output modes documented with examples

### Migration from 0.3.x

The old workflow still works:
```bash
# Old way (still supported)
wve search "Person" -o search.json
wve transcripts search.json -o transcripts/
wve report transcripts/ -s "Person"

# New way (recommended)
wve run "https://youtube.com/watch?v=..." -s "Person"
```

---

## [0.3.0] - 2026-01-15

### Added

- `wve ingest` command for arbitrary text sources (markdown, PDF, raw text)
- Substack article ingestion
- PDF text extraction

### Changed

- Improved quote extraction heuristics
- Better handling of transcript noise

---

## [0.2.0] - 2026-01-02

### Added

**Identity System**
- `wve identity create` - Create identity profiles with channels, aliases, websites
- `wve identity list` - List all identities
- `wve identity show` - Show identity details
- `wve identity add-channel` - Add YouTube channel to identity
- `wve identity add-video` - Add confirmed/rejected videos
- `wve identity delete` - Delete identity

**Discovery Commands**
- `wve discover` - Search with classification (likely/uncertain/false_positive)
- `wve confirm` - Mark videos as confirmed/rejected (batch or interactive)
- `wve fetch` - Download transcripts for confirmed videos

**Source Commands**
- `wve from-channel` - Scrape all videos from a YouTube channel
- `wve from-urls` - Process manually curated video URLs
- `wve from-rss` - Ingest from RSS/Atom feeds (YouTube RSS supported)

**Analysis Commands**
- `wve quotes` - Extract notable quotes with heuristics
- `wve themes` - Extract themes with supporting quotes
- `wve contrast` - Find contrarian/distinctive beliefs
- `wve report` - Generate comprehensive markdown report
- `wve refine` - Interactive search refinement for identity

**Persistent Store**
- `wve store save` - Save worldview extraction
- `wve store list` - List stored worldviews
- `wve store show` - Show stored worldview details
- `wve store search` - Search by name/tag
- `wve store delete` - Delete stored worldview

**Quote-Grounded Synthesis**
- `synthesize_grounded()` - LLM synthesis backed by verbatim quotes
- Every worldview point must cite actual quotes

### Changed

- Default workflow is now identity-first, not search-first
- Classification heuristics consider identity context
- All commands support `--json` for automation/AI mode
- Status messages go to stderr, data to stdout in JSON mode

### Fixed

- Identity resolution for common names
- Keyword extraction losing signal (now uses actual quotes)

---

## [0.1.0] - 2025-12-15

### Added

Initial release:
- Video search via yt-dlp
- Transcript download with VTT preprocessing
- Keyword extraction (YAKE, TF-IDF, NER)
- Semantic clustering (sentence-transformers)
- Worldview synthesis (quick/medium/deep modes)
- RAG-style Q&A with `wve ask`
- Full pipeline command
- Artifact inspection with `wve inspect`
- Transcript concatenation with `wve dump`
