# Weave v0.3.0 Implementation Quick Start

## TL;DR

Phase 0 is complete. The Weave project has been rebranded and dependencies added. 16 implementation tasks are ready in the task tracking system.

**Next step:** Start Phase 1 by implementing Task #2 (Input Ingestion Layer).

## Quick Reference

### Check Task Status
```bash
TaskList                    # See all 16 tasks
TaskGet 2                   # View detailed task #2 (input ingestion)
```

### Start a Task
```bash
TaskUpdate 2 --status in_progress    # Mark task as being worked on
# ... implement the feature ...
TaskUpdate 2 --status completed      # Mark when done
```

### View the Plan
```bash
cat REBUILD_PLAN.md                  # Full 555-line specification
head -100 REBUILD_PLAN.md            # Quick overview
```

### Test Changes
```bash
cd /Users/moritzbierling/werk/wield/weave
python3 -m pytest tests/ -v          # Run full test suite
wve --version                        # Verify command still works
```

### Commit Your Work
```bash
git add -A
git commit -m "Implement [feature]: [description]

- What was changed
- Why it was changed

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

## Phase 1 Task Order

### Task #2: Input Ingestion Layer (HIGHEST PRIORITY)
**Status:** Pending | **Depends On:** Nothing

**What:** Create `src/wve/ingest.py` with support for:
- YouTube videos (existing)
- Substack articles (new)
- Twitter threads (new)
- Markdown files (new)
- PDF documents (new)
- Plain text (new)

**Key Files to Create:**
- `src/wve/ingest.py` - Main ingestion module

**Key Classes:**
- `Source` - Data model for ingested content
- `Ingester` - Abstract base class
- `YouTubeIngester`, `SubstackIngester`, `TwitterIngester`, `MarkdownIngester`, `PDFIngester`, `TextIngester`
- `ingest_auto()` - Auto-detect and ingest

**New CLI Commands:**
```bash
wve ingest <input> -o sources/
wve ingest https://youtube.com/... -o sources/
wve ingest https://substack.com/p/... -o sources/
wve ingest ./blog.md -o sources/
wve ingest ./book.pdf -o sources/
```

**Expected Test Output:**
```bash
✓ All ingestion formats work
✓ Auto-detection is accurate
✓ Source metadata is captured
✓ CLI integration works
```

### Task #3: Configuration System
**Status:** Pending | **Depends On:** Task #2

**What:** Create `src/wve/config.py` with Pydantic models and load from `~/.config/wve/config.toml`

**Key Files to Create:**
- `src/wve/config.py` - Configuration module

**Key Classes:**
- `WVEConfig` - Main config model
- `ModelsConfig`, `DiscoveryConfig`, `ExtractionConfig`, `OutputConfig`, `CacheConfig`, `ExperimentalConfig`

**New CLI Commands:**
```bash
wve config init     # Generate default config
wve config show     # Display current settings
wve config path     # Show config file location
```

### Task #4: Explainability
**Status:** Pending | **Depends On:** Task #2-3

**What:** Make classifications transparent with component-based scoring

**Key Files to Modify:**
- `src/wve/classify.py` - Add explanation output
- `src/wve/cli.py` - Add `--explain` flag

**Key Classes to Create:**
- `ConfidenceComponent` - Individual score component
- `ClassificationExplanation` - Full explanation
- `ResolvedSource` - Video metadata with resolution

**New CLI Flag:**
```bash
wve discover "Subject" --explain     # Show reasoning
```

### Task #5: Better Error Messages
**Status:** Pending | **Depends On:** Task #2-4

**What:** Add actionable error messages with recovery suggestions

**Example Improvements:**
```
❌ Before: "yt-dlp not found"
✅ After: "yt-dlp not found. Install with: brew install yt-dlp"

❌ Before: "Search timed out"
✅ After: "Search timed out. Try: 1) Check internet, 2) Reduce --max-results, 3) Use --channel"
```

### Task #6: Progress Indicators
**Status:** Pending | **Depends On:** Task #2-5

**What:** Add Rich progress bars to long operations

**Commands to Enhance:**
- `wve fetch` - Progress bar for downloads
- `wve discover` - Status spinner for search/classification
- `wve quotes` - Progress for extraction
- `wve synthesize` - Progress for synthesis

### Task #7: Interactive Wizard
**Status:** Pending | **Depends On:** All Phase 1 tasks

**What:** Create `wve wizard` command for guided workflow

**Workflow:**
1. Identity creation
2. Discovery (search or URLs)
3. Confirmation (interactive table)
4. Analysis selection
5. Output review

## Phase 1 Success Criteria

After completing all 6 tasks, verify:

```bash
# Test ingestion
wve ingest https://youtube.com/watch?v=... -o test/
wve ingest https://example.substack.com/p/... -o test/

# Test configuration
wve config init
wve config show
cat ~/.config/wve/config.toml

# Test explainability
wve discover "Test Subject" --max-results 3 --explain

# Test error messages
wve discover "Test" --invalid-flag  # Should show helpful error

# Test progress
wve fetch test/candidates.json      # Should show progress bar

# Test wizard
wve wizard                          # Should guide through workflow

# Test suite
python3 -m pytest tests/ -v         # All tests pass
```

## File Structure After Phase 1

```
src/wve/
├── cli.py               # (unchanged in Phase 1)
├── ingest.py            # NEW (Task #2)
├── config.py            # NEW (Task #3)
├── explain.py           # NEW (Task #4)
├── classify.py          # MODIFIED (Task #4)
├── identity.py          # (unchanged)
├── search.py            # (unchanged)
├── transcripts.py       # (unchanged)
├── extract.py           # (unchanged)
├── cluster.py           # (unchanged)
├── quotes.py            # (unchanged)
├── synthesize.py        # (unchanged)
├── models.py            # (unchanged)
├── cache.py             # (unchanged)
├── store.py             # (unchanged)
└── rag.py               # (unchanged)

~/.config/wve/
└── config.toml          # NEW
```

## Testing During Implementation

### Unit Tests (Create as you go)
```bash
python3 -m pytest tests/test_ingest.py -v
python3 -m pytest tests/test_config.py -v
python3 -m pytest tests/test_explain.py -v
```

### Integration Tests (Full workflows)
```bash
# Test real ingestion workflow
wve ingest https://youtube.com/watch?v=dQw4w9WgXcQ -o test/
wve ingest test/sample.md -o test/

# Test complete pipeline
wve discover "Subject" -o candidates.json
wve fetch candidates.json -o transcripts/
wve extract transcripts/ -o extractions.json
wve cluster extractions.json -o clusters.json
```

### Regression Tests (Ensure Phase 0 still works)
```bash
# Verify backward compatibility
wve identity list
wve identity show test
wve --version
wve --help
```

## Key Design Principles

1. **Input Agnostic**: Work with any text source
2. **Backward Compatible**: Existing workflows still work
3. **Progressive Enhancement**: Each phase builds on previous
4. **User-Centric**: Clear feedback and guidance
5. **Testable**: Modular design enables testing
6. **Documented**: Every feature is documented

## Getting Help

1. **Task Details**: `TaskGet 2` (shows full specification)
2. **Full Plan**: `cat REBUILD_PLAN.md`
3. **Architecture**: See "Design Patterns" in REBUILD_PLAN.md
4. **Examples**: Check existing code in `src/wve/`

## Next Steps After Phase 1

- **Phase 2**: Build Textual TUI (Task #8)
- **Phase 3**: Create HTML reports with visualizations (Tasks #9-10)
- **Phase 4**: Refactor architecture and add versioning (Tasks #11-12)

## Timeline

- Phase 1: 1-2 weeks (6 tasks)
- Phase 2: 1 week (1 task, can overlap)
- Phase 3: 1-2 weeks (2 tasks)
- Phase 4: 1 week (2 tasks)

**Total**: 6-8 weeks for complete v0.3.0 release

---

**Start with Task #2** (Input Ingestion) - it's the foundation for everything else!
