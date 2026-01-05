# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

**Quote-Grounded Synthesis**
- `synthesize_grounded()` - LLM synthesis backed by verbatim quotes
- Every worldview point must cite actual quotes

### Changed

- Default workflow is now identity-first, not search-first
- Classification heuristics consider identity context (own channel, trusted channels, confirmed/rejected history)
- All commands support `--json` for automation/AI mode
- Status messages go to stderr, data to stdout in JSON mode

### Fixed

- Identity resolution for common names (no longer returns Kristen Bell for "Kristian Bell")
- Keyword extraction losing signal (now uses actual quotes instead of generic keywords)

## [0.1.0] - 2025-12-XX

Initial release with:
- Video search via yt-dlp
- Transcript download with VTT preprocessing
- Keyword extraction (YAKE, TF-IDF, NER)
- Semantic clustering
- Worldview synthesis (quick/medium/deep modes)
- RAG-style Q&A with `wve ask`
- Full pipeline command
