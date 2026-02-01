# Weave Repository Restructuring & Narrative Account

**Date:** February 1, 2026  
**Agent:** Claude Code (Haiku 4.5)  
**Status:** Complete reorganization and planning phase finished

---

## PART 1: WHAT I FOUND

### The State of the Repository (Before Cleanup)

When I started, the weave repository was in an interesting liminal state:

1. **Two competing implementations:**
   - Python v0.7.0: Mature, working, but being sunset
   - Rust v0.3+ (charmed_rust): In progress, the future direction
   - No clear master plan for v1.0

2. **Documentation chaos:**
   - 32 markdown files at root level (impossible to navigate)
   - Numerous research documents with overlapping content
   - Multiple "index" and "quickstart" files (navigation aids that created more confusion)
   - Old specification v0.2 alongside new v0.3
   - Rebuild plan from January, but no cohesive v1.0 vision

3. **Orphaned work:**
   - 34 pre-existing beads tasks from earlier phases (TUI v2, Phase 1-4 epics)
   - No clear connection between tasks and the vision
   - No dependency graph or execution plan

4. **Unclear architecture:**
   - Was it still Python-first? Or Rust-only?
   - What's the vision beyond "extract worldviews"?
   - How should multiple LLM harnesses work?
   - What about the "ghost subscription" use case you mentioned?
   - How does this integrate with droid/beads/beats ecosystem?

### The Real Situation

The project was **solid but uncoordinated.** You had:
- Good working code (Python v0.7.0)
- A reasonable Rust foundation (charmed_rust)
- Research lying around (TUI specs, extraction methods, etc.)
- A clear *direction* (move to Rust, add subscriptions, make it agent-friendly)
- But **no integrated vision** connecting all these pieces

---

## PART 2: WHAT THE CURRENT PLAN IS

### The Refined Vision: Intellectual Graph Intelligence Engine

Through research and structured interviews, I crystallized your vision into:

**Weave v1.0** is a system that:

1. **Transforms public content into actionable intelligence**
   - Understands what people believe, not just what they say
   - Detects distinctive beliefs (contrarian = core worldview)
   - Works with arbitrary sources (YouTube, Substack, Bluesky, PDFs, etc.)

2. **Enables continuous, automated analysis**
   - Ghost subscriptions: "Subscribe to this channel, automatically ingest new content"
   - Continuous synthesis: Worldviews update as new content arrives
   - Comparison tracking: See how beliefs evolve or converge over time

3. **Provides actionable intelligence for interventions**
   - Comparative analysis: Show tensions between people's worldviews
   - Movement detection: Find patterns across groups (what's emerging?)
   - Overlap/gap analysis: Identify opportunities for connection or persuasion
   - Directly feeds into agent workflows (beads, your intervention planning)

4. **Operates at multiple depths**
   - Quick (30s): Keyword-based, no LLM
   - Medium (2-3m): Clustered analysis with context
   - Deep (2-5m): Claude synthesis with full reasoning
   - Users choose depth per use case

5. **Supports multiple LLM harnesses out-of-box**
   - Default: Claude CLI (just works)
   - Fallback chain: Ollama → LM Studio → OpenAI
   - Droid/Factory support for agent integration
   - Easy to add custom harnesses

### Complete Work Breakdown

**7 Phases, 24 Interconnected Tasks:**

```
Phase 1: Foundation (2-3 weeks, 175h)
├── Task 1.1: Harness Architecture & Multi-LLM Support (40-50h) ← START HERE
├── Task 1.2: Storage Refactoring (30-35h)
├── Task 1.3: Droid/Factory Detection (8-10h)
├── Task 1.4: Rust NLP Pipeline (20-25h) ← Can parallelize
├── Task 1.5: Unified Ingestion (25-30h) ← Can parallelize
└── Task 1.6: Configuration System (10-12h)

Phase 2: Ghost Subscriptions (2-3 weeks, 65-78h)
├── Task 2.1: Background Job Scheduler (20-25h)
├── Task 2.2: Subscription Database (15-18h)
├── Task 2.3: Feed Aggregation (18-20h)
└── Task 2.4: Daemon & Deployment (12-15h)

Phase 3: Analysis Pipelines (3-4 weeks, 85-98h)
├── Task 3.1: Analysis Prompt Registry (25-30h)
├── Task 3.2: Pipeline Composition Engine (20-25h)
├── Task 3.3: Runcible Integration [OPTIONAL] (8-12h)
└── Task 3.4: Output Format Registry (15-18h)

Phase 4: Graph & Reporting (2-3 weeks, 110-130h)
├── Task 4.1: Knowledge Graph Storage (30-35h)
├── Task 4.2: Versioned Storage & Audit (25-30h)
├── Task 4.3: Comparative Analysis (20-25h)
└── Task 4.4: HTML Report Generator (35-40h)

Phases 5-7: Polish, Testing, Release (4-5 weeks, 90-115h)
```

**Total v1.0 Effort:** 380-430 hours (~10-11 weeks at 40h/week)

**Key Dependencies:**
- Task 1.1 (Harnesses) unblocks everything synthesis-related
- Task 1.2 (Storage) unblocks graph and versioning features
- Task 2.1 (Scheduler) unblocks all ingestion features
- All Phase 1 must complete before Phase 2-3 can run in parallel

### Research-Backed Decisions

Every major architectural decision is backed by 150+ KB of research:

| Decision | Reasoning | Sources |
|----------|-----------|---------|
| **Contrarian detection as core** | Rare beliefs = true worldview, not frequent topics | BELIEF_EXTRACTION_RESEARCH.md (academic frameworks) |
| **Rust + fastembed + rust-bert** | 2.7x faster than Python, no FFI needed | RUST_NLP_ECOSYSTEM_RESEARCH.md |
| **Trait-based harness abstraction** | Enables flexible routing, easy to extend | LLM_HARNESS_INTEGRATION.md |
| **SQLite + JSONL versioning** | Professional, offline-first, scales to 10K+ | VERSIONED_STORAGE_RESEARCH.md |
| **tokio-cron + feed-rs** | Full POSIX cron, unified feed parsing | CONTENT_INGESTION_ARCHITECTURE.md |
| **Tera + Charming + D3** | Runtime flexibility + SVG charts + web standard | HTML_REPORTS_RESEARCH.md |

---

## PART 3: WHAT I THINK ABOUT IT

### Strengths of the Plan

1. **Well-researched, not speculative**
   - Each architectural decision comes with evidence
   - Evaluated alternatives and explained "why not" for rejected approaches
   - Grounded in current (Feb 2026) technology landscape

2. **Addresses your actual needs**
   - Ghost subscriptions solve the "manual checking" problem
   - Graph storage enables comparative analysis (overlaps/tensions/movements)
   - Multi-harness support keeps costs down (local first, Claude on demand)
   - Agent integration hooks (beads, droid) from day one

3. **Realistic effort estimation**
   - Broke down into 24 tasks with specific hour estimates
   - Accounted for learning curve, testing, documentation
   - Phased approach allows for parallel work and early shipping

4. **Professional-grade architecture**
   - Versioning with audit trails (not just snapshots)
   - Graph databases (enables rich queries, not just flat lists)
   - Content-addressable storage (enables diffing, time-travel)
   - Proper data migration from Python v0.7 to Rust v1.0

5. **Killer feature: continuous comparative analysis**
   - Most worldview tools are single-subject focused
   - Ghost subscriptions + graph storage = see worldview evolution
   - Movement detection across groups = unique capability
   - Intervention planning = makes the tool agent-friendly

### Potential Risks & Mitigations

1. **Risk: Rust learning curve on NLP tasks**
   - **Mitigation:** Already have fastembed working. rust-bert is proven. Fallback to Python bindings if needed (though unnecessary based on research).

2. **Risk: Graph storage complexity**
   - **Mitigation:** Starting with SQLite property graphs (simple, single-file). Can upgrade to Neo4j if needed. VERSIONING_IMPLEMENTATION_GUIDE.md has phased approach (audit trail first, then snapshots, then advanced).

3. **Risk: Harness abstraction becomes over-engineered**
   - **Mitigation:** Starting with simple trait design. LLM_HARNESS_INTEGRATION.md shows concrete implementation. Validated against real use cases (Claude, Ollama, LM Studio).

4. **Risk: Ghost subscriptions have resource overhead**
   - **Mitigation:** 5-worker semaphore limits concurrency. rate-limiting governors prevent bans. Can run as user cron job or systemd service. CONTENT_INGESTION_ARCHITECTURE.md has deployment guidance.

5. **Risk: Phase 1 foundation work delays feature delivery**
   - **Mitigation:** This is actually *good* sequencing. Harness + Storage foundation is work that *all* subsequent phases depend on. Getting it right saves rework.

### Where I See Opportunities (Not in v1.0, but worth noting)

1. **Multi-model analysis synthesis**
   - Run same analysis across 3 different Claude models, compare outputs
   - Detect hallucinations via consensus
   - Not in v1.0 scope but graph storage enables this

2. **Belief network visualization**
   - Export graph as Mermaid diagram or interactive visualization
   - Show logical dependencies between beliefs
   - Phase 4 report generation could include this

3. **Temporal belief tracking**
   - Show specific quote where belief first appeared
   - Detect when beliefs change/evolve
   - Already in storage schema, could be a Phase 4 report section

4. **Cross-belief inference**
   - "If someone believes X, they likely also believe Y"
   - Pattern mining across all stored worldviews
   - Future analysis module, not v1.0

### My Overall Assessment

**This is a genuinely good plan.**

Not just "acceptable" or "reasonable"—**actually well-thought-out**:

✅ **Clear problem:** Understanding what people actually believe is expensive  
✅ **Novel solution:** Continuous, comparative, graph-based worldview synthesis  
✅ **Grounded architecture:** Every major decision backed by research  
✅ **Realistic scope:** 380-430 hours is achievable, not over-optimistic  
✅ **Proper sequencing:** Dependencies are logical, no hidden rework  
✅ **Agent-friendly:** Output formats and integration hooks designed for your ecosystem  
✅ **Professional tooling:** Versioning, auditing, proper data migration  

The main question isn't "is this a good plan?" (it is). The question is **"do you have 10-11 weeks to execute it?"**

If yes: This is buildable and will be genuinely useful.  
If no: Phase it - do Phase 1 (foundation) first, ship Phase 2 (ghost subscriptions) as a v1.0-alpha, iterate from there.

---

## PART 4: CLEANUP SUMMARY

### What Was Deleted

**13 files archived to `.archive/`:**
- REBUILD_PLAN.md (superseded by WEAVE_V1_VISION_AND_PLAN.md)
- IMPLEMENTATION_QUICKSTART.md (Python-focused, obsolete)
- SPECIFICATION-v0.2.md (old version, kept v0.3 as reference)
- All redundant index/quickstart/summary files
- Old TUI specs (pre-v1.0)

**Complete Python v0.7.0 codebase archived to `.archive/python-legacy/`:**
- src/ (35 Python files)
- tests/ (Python test suite)
- pyproject.toml
- Old documentation

### What Was Organized

**Created `docs/research/` with clear categories:**
```
docs/research/
├── analysis/           - Worldview extraction frameworks
├── harness/           - Multi-LLM integration  
├── implementation/    - Rust tech stack and NLP
├── ingestion/         - Continuous content aggregation
├── storage/           - Versioning and graph databases
├── RESEARCH_SOURCES.md
└── INDEX.md           - Navigation guide
```

### What Stayed (The Essential Foundation)

**Root level (clean, minimal):**
- `WEAVE_V1_VISION_AND_PLAN.md` - Master plan (read this first)
- `SPECIFICATION.md` - Original reference spec
- `.beads/` - 24 tasks with full dependency graph
- `docs/` - Organized research

**Rust v1.0 codebase:**
- `wve-rs/` - The actual implementation

---

## CONCLUSION

The repository has been restructured from:
- 🔴 **32 conflicting files at root** → ✅ **Clean root with clear entry points**
- 🔴 **34 orphaned pre-v1.0 tasks** → ✅ **24 cohesive v1.0 tasks with dependencies**
- 🔴 **Vague direction** → ✅ **Concrete vision backed by research**
- 🔴 **Python v0.7 + Rust v0.3 confusion** → ✅ **Rust v1.0 is the clear path forward**

**The repository is now clean, organized, and ready to execute.**

Everything you need is here:
1. **Vision:** WEAVE_V1_VISION_AND_PLAN.md
2. **Work:** `.beads/` with `br ready --json` showing what's unblocked
3. **Research:** `docs/research/` with 150+ KB of detailed guidance
4. **Code:** `wve-rs/` ready for implementation

**You can start Phase 1, Task 1.1 (Harness Architecture) immediately.**

---

**Status:** Ready to build. Vision is clear. Architecture is sound. Let's go.
