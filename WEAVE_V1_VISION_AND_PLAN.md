# Weave v1.0: Intellectual Graph Intelligence Engine
## Complete Vision & Implementation Plan

**Status:** Vision and planning complete. Ready for Phase 1 implementation.

**Last Updated:** 2026-02-01

---

## PART 1: THE REFINED VISION

### What Is Weave?

Weave is an **intellectual graph intelligence system** that transforms public content into actionable context for agents and humans. It answers:
- *What does this person/organization/movement actually believe?*
- *What are the tensions, overlaps, and gaps in their thinking?*
- *How can I act on this knowledge?*

### Core Capabilities (v1.0)

1. **Multi-Source Ghost Subscription** 
   - Automatically pull new content from channels, blogs, people
   - Continuous aggregation: YouTube, Substack, Bluesky, podcasts, markdown blogs, PDFs
   - Schedule with cron expressions, track changes, deduplicate

2. **Configurable Analysis Pipelines**
   - Apply proven frameworks: demonstrated interests, lie detection, contrarian analysis, movement patterns
   - User-editable TOML analysis definitions stored in `~/.config/wve/analyses/`
   - Compose analyses into chains: extract → cluster → analyze → synthesize
   - Route different analyses to different harnesses (Claude for deep, Ollama for quick)

3. **Graph-Based Storage & Querying**
   - Store worldviews as knowledge graph (entities → beliefs → concepts → evidence)
   - Query APIs: find_beliefs(entity), find_tensions(entity1, entity2), find_overlaps([entities])
   - Temporal tracking: see belief evolution over time
   - Versioned storage with audit trails

4. **Agent-Native Output**
   - JSON, markdown, HTML reports optimized for both human reading and LLM consumption
   - Beautiful interactive HTML reports with D3 network graphs, timelines, radar charts
   - Export formats: JSON, Markdown, HTML, CSV, SQL
   - Programmatic access for agent workflows

5. **Intervention Planning**
   - Detect overlaps, holes, tensions in worldviews
   - Comparative analysis across individuals (wve diff <A> <B>)
   - Movement analysis across groups (wve movement <A> <B> <C>...)
   - Suggest actions based on discovered patterns

### Multi-Harness Support (Out-of-Box)

**Default:** Claude CLI (works automatically)

**Supported Harnesses:**
- Claude (Anthropic CLI) ← Default
- Ollama (local open-source models)
- LM Studio (local inference)
- vLLM (fast local serving)
- Llamafile (single-file models)
- OpenAI (paid API)

**Compute Hierarchy:**
```
L0: Code (regex, frequency)           → free, instant
L1: Local NLP (extraction)             → free, seconds  
L2: Embeddings (clustering)            → free, minutes
L3: Local LLM (Ollama synthesis)       → free, minutes
L4: Claude/Droid (advanced analysis)   → paid, on-demand
```

### Architecture Principles

- **Modular:** Each analysis is a pluggable function
- **Composable:** Chain analyses into pipelines with conditional logic
- **Professional Tooling:** Rust-native storage, proper migrations, audit trails
- **Harness-Agnostic:** Works with any configured LLM
- **Offline-First:** SQLite-based, zero external dependencies
- **Scalable:** Proven to handle 1000+ videos, agent-accessible

---

## PART 2: RESEARCH-BACKED ARCHITECTURE

### Analysis Frameworks (From BELIEF_EXTRACTION_RESEARCH.md)

**Worldview Extraction** (3-level depth)
- Quick (30s): Keyword-based, no LLM
- Medium (2-3m): Clustered themes + context
- Deep (2-5m): Claude synthesis with full evidence

**Built-in Analyses:**
1. **Contrarian Detection** - Identify distinctive beliefs (not mainstream opinions)
2. **Demonstrated Interests** - What does this person actually care about? (frequency + exclusivity)
3. **Lie Detection** - Linguistic markers (LIWC patterns): hedging, absolutes, pronoun shifts
4. **Movement Pattern Detection** - Across 5+ subjects: shared beliefs, collective thinking
5. **Overlaps & Gaps** - Find tensions, agreements, missing perspectives
6. **Runcible Validation** (optional) - Verify AI-generated claims

### Rust Tech Stack (From RUST_NLP_ECOSYSTEM_RESEARCH.md)

**NLP & Extraction:**
- `fastembed` (v0.4) - Local embeddings ✅ Already used
- `rust-bert` (v0.23) - NER (speaker attribution, entities)
- `linfa-clustering` (v0.7) - K-means clustering (25x faster than scikit-learn)
- `yake` or regex - Keyword extraction

**Storage:**
- SQLite (built-in) + uuid (v1.x) - Versioned snapshots
- JSONL for audit logs
- JSON for artifact exports

**Efficiency:**
- LRU cache (v0.12) for embeddings - 30% speedup
- Tokio async batch processing
- Result: 2.7x faster than Python (~11s vs 30s for extraction)

### Multi-Harness Detection (From LLM_HARNESS_INTEGRATION.md)

**Strategy:** Trait-based abstraction with health checks + version detection

```rust
pub trait HarnessHandler: Send + Sync {
    async fn is_available(&self) -> bool;
    async fn list_models(&self) -> Result<Vec<ModelInfo>>;
    async fn synthesize(&self, prompt: &str) -> Result<String>;
}
```

**Routing Logic:**
- Synthesis → Best quality first (Claude > Ollama > LM Studio)
- Quick analysis → Fastest (local first, skip Claude unless needed)
- Fallback chains with automatic escalation

### Graph Storage (From VERSIONED_STORAGE_RESEARCH.md)

**Schema (SQLite Property Graph):**
```
entities: id, type (person/concept/org), name, slug
beliefs: id, entity_id, statement, confidence, evidence_count
relationships: id, entity1_id, entity2_id, type (supports/contradicts/complements)
evidence: id, belief_id, source, quote, timestamp
versions: id, entity_id, version_num, created_at, data_hash, author
```

**Features:**
- Queries: find_beliefs(entity), find_tensions(A, B), find_overlaps([A, B, C])
- Temporal: belief_version_at(entity, date)
- Diffs: 3-way merge for collaborative editing (v1.1+)
- Audit: Immutable logs of all changes

### HTML Report Tech (From HTML_REPORTS_RESEARCH.md)

**Stack:**
- **Templating:** Tera (runtime flexibility for data-to-HTML)
- **Charts:** Charming (SVG embedding) + D3.js (network graphs)
- **Styling:** Tailwind CSS (utility-first, tree-shakeable)
- **Interactivity:** Alpine.js (lightweight) for dark mode, filtering, search
- **Target:** < 2MB reports (responsive, WCAG AA accessible)

**Report Sections:**
1. Executive summary (TL;DR)
2. Theme network graph (force-directed, interactive)
3. Timeline of belief emergence
4. Radar chart (multi-dimensional worldview)
5. Heatmap (theme coverage by source)
6. Key concepts catalog (people, works, theories mentioned)

### Continuous Ingestion (From CONTENT_INGESTION_ARCHITECTURE.md)

**Stack:**
- `tokio-cron-scheduler` (v0.10+) - Full POSIX cron support
- `feed-rs` (v0.13+) - RSS/Atom/JSON auto-detection
- `governor` (v0.7+) - Rate limiting (10 req/sec per domain)
- `backoff` (v0.4+) - Exponential retry (100ms → 60s)
- SQLite subscriptions table (persistent, survives restarts)

**Worker Pool:** 5 concurrent fetches with semaphore limiting

**Deployment:** systemd (Linux) + launchd (macOS) daemons with health checks

---

## PART 3: COMPLETE WORK BREAKDOWN

### Phase 1: Foundation & Compatibility (2-3 weeks, ~175 hours)

**Goal:** Professional architecture foundation. After this phase, weave works with multiple harnesses, proper storage, and can extract worldviews.

**Task 1.1: Harness Architecture & Multi-LLM Support** (40-50h)
- Implement trait-based harness abstraction
- Detect & support: Claude, Ollama, LM Studio, vLLM, Llamafile, OpenAI
- Default Claude with graceful fallback chain
- Health checks + version detection
- CLI: `wve harnesses` (list available)
- **Research:** LLM_HARNESS_INTEGRATION.md sections 1-3
- **Blocks:** All synthesis features

**Task 1.2: Python Format Compatibility & Storage Refactoring** (30-35h)
- Migrate from Python pickle to professional Rust storage
- Support reading old Python extractions during migration
- Implement uuid, audit trail logging (JSONL), snapshot versioning
- SQLite schema for versioned storage
- **Research:** VERSIONED_STORAGE_RESEARCH.md + VERSIONING_IMPLEMENTATION_GUIDE.md Phase 1
- **Blocks:** Advanced storage features

**Task 1.3: Droid/Factory Harness Detection** (8-10h)
- Add factory-rs based harness detection
- Review Openclaw patterns
- Support droid as first-class harness
- **Depends on:** 1.1
- **Blocks:** Agent integration

**Task 1.4: Rust NLP Pipeline Foundation** (20-25h)
- Integrate fastembed (already in place) + rust-bert for NER
- Implement quote extraction, keyword extraction
- Setup linfa K-means, LRU embedding cache
- Benchmark: 2.7x faster than Python
- **Research:** RUST_NLP_ECOSYSTEM_RESEARCH.md + RUST_CODE_EXAMPLES.md
- **Blocks:** Extraction features

**Task 1.5: Unified Ingestion Layer** (25-30h)
- Support: YouTube, Substack, Bluesky, markdown, PDF, plain text
- Auto-detect format with `ingest_auto()`
- CLI: `wve ingest <input> -o sources/`
- **Research:** SPECIFICATION.md section 4.1.2
- **Blocks:** Ghost subscription

**Task 1.6: Configuration System v2** (10-12h)
- TOML config: ~/.config/wve/config.toml
- Sections: models, discovery, extraction, analyses, cache, harness routing
- Commands: `wve config init/show/edit/validate`
- **Depends on:** 1.1, 1.4
- **Blocks:** Advanced features

### Phase 2: Ghost Subscription & Ingestion Pipeline (2-3 weeks, ~65-78 hours)

**Goal:** Continuous content ingestion working. Users can subscribe to sources and get automated updates.

**Task 2.1: Background Job Scheduler & Worker Pool** (20-25h)
- tokio-cron-scheduler v0.10+ (POSIX cron expressions)
- governor v0.7+ (rate limiting: 10 req/sec)
- 5-worker semaphore, graceful shutdown
- State persistence (survives restarts)
- **Research:** CONTENT_INGESTION_ARCHITECTURE.md + INGESTION_CODE_PATTERNS.md
- **Depends on:** 1.5
- **Blocks:** 2.2, 2.3

**Task 2.2: Subscription Management Database** (15-18h)
- SQLite schema: subscriptions, feed_items, metadata
- Enable/disable, retry logic (10 strikes = disabled)
- CLI: `wve subscribe <url> --schedule <cron> --tags <tags>`
- **Depends on:** 1.2, 2.1
- **Blocks:** 2.3

**Task 2.3: Feed Aggregation & Change Detection** (18-20h)
- feed-rs v0.13+ (RSS/Atom/JSON auto-detect)
- YouTube RSS feeds, Substack RSS, Podcast Index integration
- SHA256 content deduplication
- Incremental pulls (filter by timestamp)
- **Research:** INGESTION_CODE_PATTERNS.md
- **Depends on:** 2.2
- **Blocks:** Ghost subscription goes live

**Task 2.4: Daemon & Deployment Support** (12-15h)
- systemd service file (Linux)
- launchd plist (macOS)
- Health check endpoint (optional warp HTTP server)
- Monitoring & error alerting
- **Depends on:** 2.1, 2.2, 2.3
- **Blocks:** Production deployment

### Phase 3: Analysis Framework & Configurable Pipelines (3-4 weeks, ~85-98 hours)

**Goal:** Users can define custom analyses and compose them into pipelines. Built-in analyses cover worldview extraction, contrarian detection, lie detection, etc.

**Task 3.1: Analysis Prompt System & Registry** (25-30h)
- User-editable TOML in ~/.config/wve/analyses/
- Built-in analyses (from BELIEF_EXTRACTION_RESEARCH.md):
  - Worldview extraction (quick/medium/deep)
  - Contrarian detection (distinctiveness scoring)
  - Demonstrated interests analysis
  - Lie detection (LIWC linguistic patterns)
  - Movement pattern detection (5+ subjects)
  - Overlaps & gaps analysis
- Analysis registry with enable/disable
- CLI: `wve analyses list/show/edit`
- **Depends on:** 1.1, 1.6
- **Blocks:** 3.2, 3.3

**Task 3.2: Pipeline Composition Engine** (20-25h)
- YAML pipeline definitions: [extract] → [cluster] → [analyze:interests] → [synthesize]
- Routing rules (which analyses use which harness)
- Conditional logic based on extracted data
- CLI: `wve run --pipeline <name>`
- **Depends on:** 3.1
- **Blocks:** Advanced workflows

**Task 3.3: Runcible API Integration (Optional, p3)** (8-12h)
- Research: What does Runcible provide? (verification layer for AI outputs)
- Integrate as optional validation analysis
- Can defer if lower priority
- **Depends on:** 3.1

**Task 3.4: Output Format Registry** (15-18h)
- Pluggable renderers: JSON, Markdown, HTML, CSV, SQL
- Trait-based `Renderer` with `register()` pattern
- Easy to add custom formats
- **Depends on:** 1.1
- **Blocks:** Export features

### Phase 4: Graph-Based Storage & Advanced Features (2-3 weeks, ~110-130 hours)

**Goal:** Professional graph storage with versioning, comparative analysis, beautiful reports.

**Task 4.1: Knowledge Graph Storage (SQLite Property Graph)** (30-35h)
- Schema: entities (people, concepts, orgs) + beliefs + relationships + evidence
- Query APIs: find_beliefs(entity), find_tensions(A, B), find_overlaps([A, B, C])
- Temporal tracking: belief_version_at(entity, date)
- Relationships: supports/contradicts/complements
- **Research:** VERSIONED_STORAGE_RESEARCH.md section 6
- **Depends on:** 1.2
- **Blocks:** Advanced queries, comparative analysis

**Task 4.2: Versioned Storage & Auditing** (25-30h)
- Content-addressable snapshots (Phase 1 audit trail → Phase 2 diffs)
- Immutable audit logs (who, what, when, why)
- JSON diff library (json-patch RFC 6902)
- Rollback capability
- Three-way merge (defer to v1.1)
- **Research:** VERSIONING_IMPLEMENTATION_GUIDE.md phases 1-3
- **Depends on:** 1.2, 4.1
- **Blocks:** Rollback, comparative diffs

**Task 4.3: Comparative Analysis System** (20-25h)
- `wve diff <slug1> <slug2>` with rich output
- `wve movement <slug1> <slug2> <slug3>...` (emergent patterns)
- Visualize: tensions, agreements, unique beliefs
- Intervention suggestions (based on gaps & overlaps)
- **Depends on:** 4.1, 4.2
- **Blocks:** None

**Task 4.4: HTML Report Generator & Visualizations** (35-40h)
- Tera templating + Charming (SVG) + Tailwind CSS + Alpine.js
- Report sections:
  - Executive summary
  - Theme network graph (D3 force-directed, interactive)
  - Timeline (belief emergence over time)
  - Radar chart (multi-dimensional worldview)
  - Heatmap (theme coverage by source)
  - Key concepts catalog (filterable)
- Dark/light mode toggle, responsive design, WCAG AA accessibility
- Export to PDF (browser print)
- **Research:** HTML_REPORTS_RESEARCH.md (complete tech stack)
- **Depends on:** 1.1, 3.4
- **Blocks:** Beautiful outputs

### Phase 5: Rich Terminal UI (charmed_rust) (1-2 weeks, ~25-30 hours)

**Goal:** Modern TUI with inline prompts, interactive candidate review, keybind customization.

**Task 5.1: TUI v2 Refresh & Modernization** (25-30h)
- Replace old wizard with inline keyboard-driven prompts
- Interactive candidate review with multi-select (space bar)
- Keybind configuration (customizable in ~/.config/wve/)
- Progress bars for long operations
- Undo/redo stack
- **See:** Existing TUI v2 beads (bd-9ds through bd-3r2)
- **Depends on:** 1.4, 2.3
- **Blocks:** User experience

### Phase 6: Integration & Testing (1-2 weeks, ~50-65 hours)

**Goal:** Comprehensive testing, documentation, and performance optimization.

**Task 6.1: End-to-End Testing & Quality Assurance** (20-25h)
- Test workflows: single-subject → comparative → movement → interventions
- Fixture datasets: Burlingame, Skinner, synthetic corpus
- Performance benchmarks:
  - Extraction: <30s for 10 videos
  - HTML report generation: <2s
  - Graph queries: <100ms
- Regression test suite
- **Research:** SPECIFICATION.md section 9
- **Depends on:** All phases complete

**Task 6.2: Documentation & API Reference** (15-18h)
- README.md rewrite (refined vision)
- SPECIFICATION.md v1.0 update
- AGENTS.md (integration guide for agents)
- API documentation (harness trait, analysis registry, graph queries)
- Migration guide (v0.3 → v1.0)
- **Depends on:** 6.1

**Task 6.3: Performance Optimization & Profiling** (15-20h)
- Profile NLP pipeline, storage queries, HTML generation
- Optimize hot paths (embedding cache hits, batch processing)
- Memory targets: <500MB peak
- Throughput targets: Extract 100 videos in <5 minutes
- **Depends on:** 6.1

### Phase 7: Release & Cutover (1 week, ~15-20 hours)

**Goal:** Seamless migration from v0.3 to v1.0, public release.

**Task 7.1: Migration from v0.3 to v1.0** (10-12h)
- Automated migration tool (Python format → Rust storage)
- Data validation scripts (verify all data transferred)
- Rollback plan and testing
- **Depends on:** 1.2, 4.2, 6.1
- **Blocks:** 7.2

**Task 7.2: Release Preparation & Publishing** (5-8h)
- Version bump (0.3 → 1.0)
- CHANGELOG generation (from commits)
- GitHub release notes
- Announcement & community feedback loop
- **Depends on:** 7.1, 6.2
- **Blocks:** None

---

## PART 4: READY STATE

### What's Ready NOW
- ✅ Complete refined vision (research-backed)
- ✅ 24 tasks created in beads with full dependencies
- ✅ Research documents for all major components:
  - BELIEF_EXTRACTION_RESEARCH.md (39 KB, frameworks & theories)
  - RUST_NLP_ECOSYSTEM_RESEARCH.md (32 KB, Rust libraries)
  - LLM_HARNESS_INTEGRATION.md (40 KB, multi-harness design)
  - HTML_REPORTS_RESEARCH.md (comprehensive tech stack)
  - VERSIONED_STORAGE_RESEARCH.md (36 KB, professional storage)
  - CONTENT_INGESTION_ARCHITECTURE.md (continuous ingestion)
- ✅ Ready-to-use code examples for every major component
- ✅ Dependency graph configured in beads (use `bv --robot-plan` to see execution order)

### Next Steps
1. **Review this vision document** - Does it align with your goals?
2. **Start Phase 1, Task 1.1:** Harness architecture (has no blockers, unblocks everything else)
3. **In parallel, start Phase 1 Tasks 1.4, 1.5:** NLP foundation and ingestion layer
4. **Check ready work:** `br ready --json` shows tasks with no blockers
5. **Track progress:** `bv --robot-insights` shows critical path and bottlenecks

### Execution Pattern (Compounding Engineering)
- Each completed task makes subsequent tasks easier
- Phase 1 foundations enable parallel work in Phases 2-4
- Dependencies ensure no rework or conflicts
- Estimated total v1.0 effort: **380-430 hours** (~10-11 weeks at 40h/week)

---

## PART 5: KEY RESEARCH FINDINGS

### Most Impactful Discoveries

1. **Contrarian Detection is the Real Signal**
   - Users assume frequent topics = core beliefs. Wrong.
   - **Core worldview = rare, distinctive beliefs** (top 25% uniqueness = true worldview)
   - Implementation: TF-IDF distinctiveness scoring

2. **Rust NLP is Production-Ready**
   - fastembed + rust-bert + linfa = 2.7x faster than Python
   - Smaller memory footprint
   - No Python FFI needed

3. **Multi-Harness is Essential**
   - Different analyses need different harnesses (quality vs speed)
   - Fallback chains critical (Claude → Ollama → LM Studio)
   - Trait-based abstraction is the right pattern

4. **SQLite Versioning Scales**
   - Content-addressable snapshots sufficient for 10K+ worldviews
   - Audit trails cost ~100 bytes per change
   - Time-travel queries possible with proper schema

5. **Ghost Subscriptions = Killer Feature**
   - Continuous ingestion changes game entirely
   - Users don't have to remember to check back
   - Enables comparative analysis across time

### Tools Worth Understanding
- **feed-rs:** Unified RSS/Atom/JSON parsing (not obvious there's one lib that does all)
- **Charming:** SVG generation from Rust (underrated, cleaner than D3 for static charts)
- **Tera:** Runtime templating is perfect for reports (compile-time checking unnecessary)
- **Tokio-cron:** Full POSIX cron in async Rust (critical for ghost subscriptions)

---

## SUMMARY

Weave v1.0 is positioned to be the most sophisticated open-source worldview analysis tool available. Research-backed architecture, professional-grade implementation, agent-native design.

**The vision is achievable, well-researched, and ready for execution.**

```
WEAVE: Intellectual Graph Intelligence Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Understand what people believe.
Detect tensions and overlaps.
Make meaningful interventions.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

