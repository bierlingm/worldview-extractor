# Weave v1.0 - Intellectual Graph Intelligence Engine

**Status:** Planning complete, Phase 1 ready to start

## Quick Start

1. **Read the plan:** WEAVE_V1_VISION_AND_PLAN.md
   - Complete vision, architecture, and implementation breakdown
   - 7 phases, 24 tasks, 380-430 hours

2. **View work tracking:** beads
   - `br ready --json` - See what's ready to start
   - `br show <task-id>` - See task details
   - `bv --robot-plan` - See execution order

3. **Research & Implementation Guides:** docs/research/
   - analysis/ - Worldview extraction frameworks
   - harness/ - Multi-LLM integration patterns
   - implementation/ - Rust tech stack and code examples
   - ingestion/ - Continuous content aggregation
   - storage/ - Versioned storage and graph databases

## What's Weave?

Transform public content into actionable intelligence about what people believe.

**Core capabilities:**
- Multi-source ghost subscriptions (YouTube, Substack, Bluesky, PDFs)
- Configurable analysis pipelines (contrarian detection, lie detection, movement patterns)
- Graph-based storage with versioning and temporal queries
- Beautiful HTML reports with interactive visualizations
- Out-of-the-box Claude support with fallback harnesses

## Architecture

- **Language:** Rust (production-grade)
- **Storage:** SQLite + JSONL (versioned, professional)
- **NLP:** fastembed + rust-bert + linfa (2.7x faster than Python)
- **Scheduling:** tokio-cron + feed-rs (continuous ingestion)
- **UI:** charmed_rust TUI + HTML reports
- **LLMs:** Claude (default) → Ollama → LM Studio (fallback chain)

## Files

- **WEAVE_V1_VISION_AND_PLAN.md** - Master plan, read this first
- **SPECIFICATION.md** - Original spec (reference)
- **docs/research/** - Deep dives on each architecture component
- **.beads/** - Work tracking (24 tasks, fully dependency-mapped)
- **.archive/** - Legacy Python v0.7.0 and old docs

## Next Steps

```bash
# Check available work
br ready --json

# Start Phase 1, Task 1.1 (Harness Architecture)
br show bd-39k

# See execution plan
bv --robot-plan
```

---

**Everything you need is here. Vision is clear. Research is thorough. Let's build.**
