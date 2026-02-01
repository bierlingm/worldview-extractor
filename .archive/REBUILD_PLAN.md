# Weave v0.3.0 Comprehensive Rebuild Plan

**Status:** Phase 0 Complete ✅
**Timeline:** 6-8 weeks for full rebuild
**Current Version:** 0.3.0
**Previous Version:** 0.2.0

## Executive Summary

Weave is a comprehensive worldview synthesis tool being rebuilt from the ground up. The rebuild spans 4 phases and transforms Weave from a video-focused tool into an input-agnostic synthesis engine that works with arbitrary text sources (videos, articles, tweets, books, podcasts, PDFs).

### Key Improvements

1. **Input-agnostic ingestion** - Support for YouTube, Substack, Twitter, Markdown, PDF
2. **Rich terminal UI** - Interactive Textual TUI for candidate review
3. **Beautiful visualizations** - HTML reports with Chart.js and D3.js
4. **Hierarchical synthesis** - Core themes, named concepts, contrarian analysis
5. **Clean architecture** - Modular CLI, plugin system, versioned storage
6. **Better UX** - Progress indicators, explainability, helpful errors

## Phase 0: Complete ✅

### Completed Tasks

1. **Rename project** - worldview-extractor → weave
2. **Update package** - name, version (0.2.0 → 0.3.0), description
3. **Add dependencies** - textual, jinja2, markupsafe, pytest-asyncio
4. **Update documentation** - README, pyproject.toml
5. **Maintain backward compatibility** - CLI command still `wve`
6. **Commit** - Git commit: 52dac96

### Directory Structure

```
/Users/moritzbierling/werk/wield/weave/
├── src/wve/              # Python package
├── tests/                # Test suite
├── data/                 # Sample datasets
├── .beads/              # Beads issue tracker (git-backed)
├── pyproject.toml       # Updated with new dependencies
├── README.md            # Rebranded documentation
└── REBUILD_PLAN.md      # This file
```

## Phase 1: Foundation & Quick Wins (Weeks 1-2)

### Overview

Implement core features that enable basic workflows: ingestion, configuration, explainability, error handling, progress, and guided workflows.

### Task #2: Unified Input Ingestion Layer

**Goal:** Make Weave source-agnostic by supporting arbitrary text inputs.

**Deliverables:**
- `src/wve/ingest.py` - Source models and Ingester ABC
- Specific ingester implementations:
  - `YouTubeIngester` - Extract transcript from YouTube videos
  - `SubstackIngester` - Parse Substack articles
  - `TwitterIngester` - Extract tweet threads
  - `MarkdownIngester` - Parse markdown blog posts
  - `PDFIngester` - Extract text from PDFs
  - `TextIngester` - Fallback for plain text
- `ingest_auto()` - Auto-detect format
- CLI: `wve ingest <input> -o sources/`

**Example Usage:**
```bash
wve ingest https://youtube.com/watch?v=... -o sources/
wve ingest https://substackurl.com/p/... -o sources/
wve ingest https://twitter.com/user/status/... -o sources/
wve ingest ./blog-posts/*.md -o sources/
wve ingest ./book.pdf -o sources/
wve ingest --urls-file mixed-sources.txt -o sources/
```

### Task #3: Configuration System

**Goal:** Centralize settings in ~/.config/wve/config.toml

**Deliverables:**
- `src/wve/config.py` - Pydantic config models
- `~/.config/wve/config.toml` - Default configuration
- CLI commands: `wve config init/show/path`

**Config sections:**
- `[models]` - LLM, embedding model settings
- `[discovery]` - Search parameters, depth, max videos
- `[extraction]` - Quote/theme extraction tuning
- `[output]` - Formatting, visualization options
- `[cache]` - Cache strategy, location
- `[experimental]` - Feature flags for Phase 2+

### Task #4: Explainability

**Goal:** Show transparent classification reasoning.

**Deliverables:**
- `src/wve/explain.py` - Explanation models
- Enhanced `src/wve/classify.py` - Return explanations
- CLI flag: `--explain` to `wve discover`

**Features:**
- Component-based scoring (channel + title + format + history)
- Detailed reasoning for each component
- Decision path tracking
- Rich color-coded output (green/yellow/red)
- Source resolution to titles, URLs, timestamps

**Example Output:**
```
Classification: likely (85%)
Reason:
  • Channel Match +40% (from subject's verified channel)
  • Title Match +30% (exact name found in title)
  • Format Match +15% (interview/podcast detected)

Sources:
  [1] https://youtube.com/watch?v=... - "Interview with [Subject]" - 12:34
```

### Task #5: Better Error Messages

**Goal:** Provide actionable recovery suggestions.

**Deliverables:**
- Enhanced error classes with `suggestion` field
- Global CLI error handler
- Common error scenarios with recovery steps
- `--verbose` flag for debugging

**Examples:**
- "yt-dlp not found" → "Install with: `brew install yt-dlp`"
- "Ollama not available" → "Start with: `ollama serve llama2`"
- "Search timed out" → "Try: 1) Check internet, 2) Reduce --max-results, 3) Use --channel"
- "Identity not found" → "Create first: `wve identity create <name>`"

### Task #6: Progress Indicators

**Goal:** Show progress for long-running operations.

**Deliverables:**
- Rich progress bars for:
  - `wve fetch` - "Downloading X/N: [title]..." with speed/ETA
  - `wve discover` - "Searching... (N results)" → "Classifying X/Y candidates..."
  - `wve quotes` - "Processing transcripts X/N..." with count
  - `wve synthesize` - "Clustering themes..." → "Generating narrative..."

**Features:**
- Brief, non-intrusive progress displays
- Support `--quiet` flag to suppress
- Meaningful units (videos, candidates, quotes, themes)
- TTY detection (no output to pipes)

### Task #7: Interactive Wizard Workflow

**Goal:** Guided workflow for new users.

**Deliverables:**
- `wve wizard` command
- Five-step workflow:
  1. Identity creation (name, channels)
  2. Discovery (search or URLs)
  3. Confirmation (interactive table)
  4. Analysis selection (quotes/themes/report/all)
  5. Output review

**Features:**
- Rich prompts and tables
- Interactive candidate preview
- Multi-select with space bar
- Wizard preferences storage
- Summary report after completion

**Example Flow:**
```bash
$ wve wizard
Welcome to Weave Wizard!

Step 1: Identity
What's the subject's name? EM Burlingame
Add any channel URLs? https://youtube.com/@...
[Preview identity]

Step 2: Discovery
Search YouTube or provide URLs? [search] / [urls]
Configure depth? [quick] / [medium] / [thorough]
Max videos? 10

Step 3: Confirmation
[Interactive table of 8 candidates]
Select candidates: [checked] 7/8

Step 4: Analysis
What analysis? [all]

Step 5: Output
✅ Generated:
  - transcripts/ (8 files)
  - candidates.json
  - worldview.json
  - worldview.md
```

### Success Criteria (Phase 1)

- [ ] Input ingestion works for all 6 formats
- [ ] Config system generates and loads correctly
- [ ] `--explain` shows meaningful classification reasoning
- [ ] Error messages are helpful with suggestions
- [ ] Progress bars appear and update smoothly
- [ ] Wizard completes end-to-end workflow
- [ ] All Phase 1 tests pass
- [ ] No regressions in Phase 0

## Phase 2: Rich Terminal UI (Weeks 3-4)

### Task #8: Textual TUI for Candidate Review

**Goal:** Interactive terminal UI for reviewing and confirming candidates.

**Deliverables:**
- `src/wve/tui/` directory structure
  - `app.py` - WveApp main Textual application
  - `widgets.py` - Custom widgets
  - `bindings.py` - Keyboard shortcuts
  - `theme.py` - Color scheme
  - `actions.py` - Undo/redo stack

**Component Hierarchy:**
```
WveApp
├── HeaderWidget (identity, status)
├── MainLayout
│   ├── CandidateListView (left 40%)
│   │   ├── SearchInput
│   │   ├── FilterTabs (likely/uncertain/all)
│   │   └── CandidateDataTable
│   ├── PreviewPane (right top 60%)
│   │   ├── VideoMetadataWidget
│   │   ├── ConfidenceBreakdownWidget
│   │   └── ClassificationReasonWidget
│   └── TranscriptPreview (collapsible)
└── FooterWidget (keyboard shortcuts)
```

**Keyboard Bindings:**
- `j`/Down - Move down
- `k`/Up - Move up
- `Space` - Toggle selection
- `y` - Confirm selected
- `n` - Reject selected
- `u` - Undo last action
- `r` - Redo last undone action
- `?` - Show help
- `q` - Quit

**Features:**
- Load candidates from `candidates.json`
- Multi-select with visual feedback
- Filter by classification (likely/uncertain/false_positive)
- Sort by confidence, title, channel
- Undo/redo stack for all changes
- Save to `confirmed.json` and `rejected.json` on exit
- Auto-update identity files

### Success Criteria (Phase 2)

- [ ] TUI launches with `wve tui candidates.json`
- [ ] Keyboard navigation works (hjkl, arrows, space)
- [ ] Confidence breakdown shows component scores
- [ ] Sources resolve to titles, URLs, timestamps
- [ ] Undo/redo functional (u/r keys)
- [ ] Multi-select works and saves correctly
- [ ] 90%+ test coverage for TUI code
- [ ] Phase 1 still works (backward compatible)

## Phase 3: Visual Outputs (Weeks 5-6)

### Task #9: Hierarchical Worldview Synthesis

**Goal:** Generate coherent, structured worldview narratives.

**Deliverables:**
- `src/wve/synthesize_hierarchical.py` - Main synthesis logic
- Enhanced models in `src/wve/models.py`:
  - `WorldviewTheme` - Title, description, beliefs, confidence
  - `WorldviewPoint` - Individual belief with quotes, contrarian score
  - `NamedConcept` - People, works, concepts mentioned
  - `HierarchicalWorldview` - Complete structured worldview

**Output Structure:**
```
1. Executive Summary (3-5 sentences TL;DR)
2. Core Themes (3-5 major themes)
   - Theme 1: Reality & Knowledge
     - Belief 1.1: Reality is fundamentally linguistic
       - Evidence: 9 sources, 14 quotes
       - Contrarian score: 0.87 (HIGH)
       - Quote 1: "The map is not the territory, but..."
   - Theme 2: ...
3. Named Concepts Catalog
   - People: Carl Jung, ...
   - Concepts: Logos, Abraxas, ...
   - Works: "Psychology and Alchemy", ...
4. Contrarian Highlights
   - Most distinctive beliefs
   - Higher confidence + distinctiveness
```

**Functions:**
- `synthesize_hierarchical(transcript_dir, subject)` → HierarchicalWorldview
- `detect_named_concepts(quotes, entities)` → list[NamedConcept]
- `score_contrarian(point, mainstream_corpus=None)` → float (0.0-1.0)
- `generate_executive_summary(themes, subject)` → str

### Task #10: HTML Report Generator

**Goal:** Beautiful, interactive HTML reports with visualizations.

**Deliverables:**
- `src/wve/renderers/html.py` - HTMLRenderer class
- `src/wve/templates/` directory:
  - `base.html` - Layout and base styles
  - `worldview_report.html` - Main report template
  - `components/` - Reusable components
  - `css/` - Styles
  - `js/` - Interaction scripts

**Charts to Implement:**
1. **Theme Timeline** - When concepts first appear (horizontal bar)
2. **Theme Frequency** - Word count distribution (bar chart)
3. **Confidence Scores** - Radar chart for worldview points
4. **Video Coverage** - Stacked bar showing themes per video
5. **Theme Network** - D3.js force-directed graph (nodes=themes, edges=co-occurrence)

**Report Sections:**
- Executive Summary with theme network graph
- Core Worldview (hierarchical with theme icons)
- Distinctive & Contrarian Views (with heatmap)
- Key Concepts catalog (filterable table)
- Supporting Quotes (with timeline, filterable by theme)

**Features:**
- Responsive design (mobile-friendly)
- Dark/light theme toggle
- Filterable by theme
- Export as PDF (via browser print)
- Embedded CSS/JS (no external deps except CDN charts)
- Interactive charts with tooltips

**CLI Command:**
```bash
wve report transcripts/ -s "Name" --format html -o report.html
```

### Success Criteria (Phase 3)

- [ ] HTML reports render in all major browsers
- [ ] Charts are readable and informative
- [ ] Hierarchical worldview matches manual quality
- [ ] Contrarian detection finds 80%+ distinctive views
- [ ] Named concepts 90%+ accurate
- [ ] Responsive design works on mobile
- [ ] Phase 1-2 features still work
- [ ] Performance: <2s report generation for 50 videos

## Phase 4: Architecture Refactor (Weeks 7-8)

### Task #11: CLI Modularization

**Goal:** Reduce cli.py from 2,239 to <300 lines.

**Deliverables:**
- Create `src/wve/commands/` directory:
  - `identity.py` - identity create/list/show/delete/add-channel/add-video
  - `discovery.py` - discover/confirm/fetch/search
  - `sources.py` - from-channel/from-urls/from-rss/ingest
  - `analysis.py` - extract/cluster/synthesize
  - `output.py` - report/export/dump
  - `interactive.py` - ask/search/refine
  - `storage.py` - store (show/versions/diff)
- Refactored `cli.py` - <300 lines, entrypoint only

**Benefits:**
- Each module <300 lines (maintainable)
- Clear separation of concerns
- Easier to test and modify
- Reduced cognitive load
- Enables plugin system

### Task #12: Versioned Storage

**Goal:** Track worldview evolution over time.

**Deliverables:**
- Enhanced `src/wve/store.py`:
  - `WorldviewVersion` model
  - `save_worldview_version()`, `get_worldview_version()`
  - `list_worldview_versions()`, `diff_worldview_versions()`

**CLI Commands:**
```bash
wve store versions <slug>
wve store show <slug> --version 2
wve store diff <slug> --versions 1,3
wve export <slug> --version 2 --format html
```

**Benefits:**
- Track evolution of worldview over time
- A/B test synthesis methods
- Rollback to previous versions
- Support "what if" analysis

### Success Criteria (Phase 4)

- [ ] cli.py reduced to <300 lines (84% reduction)
- [ ] All commands work after refactor
- [ ] Plugin system supports 3+ renderers
- [ ] Versioning tracks changes correctly
- [ ] Zero data loss during migration
- [ ] 100% backward compatibility with v0.2
- [ ] All Phase 1-3 features still work
- [ ] End-to-end pipeline works: discover → fetch → synthesize → export (all formats)

## Testing & Quality

### Test Coverage

- **Unit tests** - Each module >80% coverage
- **Integration tests** - Full pipeline workflows
- **End-to-end tests** - Real data validation

### Performance Targets

- HTML report generation: <2s for 50 videos
- Hierarchical synthesis: <30s for 50 videos (with Ollama)
- TUI rendering: <500ms for 100 candidates
- Ingest operations: <1s per source

### Quality Validation

- Run existing test suite after each phase
- Manual testing with data/eridanus/ and data/skinner/ datasets
- Compare hierarchical worldview to data/eridanus/worldview-manual.md
- Validate contrarian detection accuracy (80%+ target)
- Check named concepts precision (90%+ target)

## Documentation

### Files to Update

1. **README.md** - New vision, examples, screenshots
2. **SPECIFICATION-v0.3.md** - Complete spec with all features
3. **AGENTS.md** - New commands organized by category
4. **Skill documentation** - `~/.agents/skills/wv/SKILL.md`
5. **CHANGELOG.md** - Release notes for v0.3.0
6. **Migration guide** - v0.2 → v0.3 upgrade instructions

### Documentation Structure

- **Quick Start** - 5-minute workflow
- **Installation** - Dependencies and setup
- **Command Reference** - All commands with examples
- **Workflows** - Common use cases (researcher, writer, analyst)
- **Configuration** - config.toml options
- **Plugin Development** - Custom renderer guide
- **Architecture** - System design overview

## Success Metrics

### Feature Completeness
- [x] Phase 0: Rebrand ✅
- [ ] Phase 1: Foundation (6 tasks)
- [ ] Phase 2: TUI (1 task)
- [ ] Phase 3: Visual Outputs (2 tasks)
- [ ] Phase 4: Refactor (2 tasks)

### Code Quality
- [ ] No regressions (all tests pass)
- [ ] >80% test coverage
- [ ] Zero security vulnerabilities
- [ ] Clean code (linting, formatting)

### User Experience
- [ ] Intuitive workflow
- [ ] Clear error messages
- [ ] Fast performance
- [ ] Beautiful output
- [ ] Well-documented

### Adoption
- [ ] Open-source release (GitHub)
- [ ] Example reports with public figures
- [ ] Community feedback integration
- [ ] v0.3.0 release announcement

## Version History

### v0.2.0 (Current)
- Basic video-focused worldview extraction
- Video search and transcript download
- Quote extraction and clustering
- Flat worldview synthesis
- CLI interface

### v0.3.0 (This Rebuild)
- Input-agnostic ingestion (6+ formats)
- Interactive Textual TUI
- Hierarchical worldview synthesis
- HTML report generation with charts
- Modular architecture with plugin system
- Versioned storage
- Enhanced explainability
- Better error handling and UX

## Timeline Estimate

- **Phase 0**: ✅ Complete (day 1)
- **Phase 1**: 1-2 weeks (6 tasks)
- **Phase 2**: 1 week (1 task, can parallelize with Phase 1)
- **Phase 3**: 1-2 weeks (2 tasks, depends on Phase 1-2)
- **Phase 4**: 1 week (2 tasks, final cleanup)
- **Total**: 6-8 weeks for comprehensive rebuild

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Textual learning curve | Start simple, iterate incrementally |
| HTML template complexity | Minimal template first, expand gradually |
| Plugin system over-engineered | Build 2-3 real plugins first |
| Hierarchical synthesis quality | A/B test with flat synthesis, tune prompts |
| Migration breaks workflows | Extensive backward compatibility testing |
| Performance issues | Profile early, optimize hot paths |
| Test coverage gaps | Write tests as features are added |

## Next Steps

1. **Immediately**: Review and approve this plan
2. **Week 1**: Start Phase 1 (Task #2-7)
   - Focus on ingestion and configuration first
   - Test with real data
   - Commit frequently
3. **Week 2-3**: Phase 1 completion + Phase 2 start
4. **Week 4-6**: Phase 2-3 parallel work
5. **Week 7-8**: Phase 4 (refactor and finalization)
6. **Post-release**: Community feedback, bug fixes, documentation

---

**Last Updated**: 2025-01-28
**Status**: Plan Complete - Ready for Phase 1 Implementation
**Next Milestone**: Complete Task #2 (Input Ingestion)
