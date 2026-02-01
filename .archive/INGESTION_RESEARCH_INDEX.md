# Content Ingestion Research: Document Index

**Complete research package for continuous content ingestion architecture.**

---

## Documents in This Research

### 1. **INGESTION_QUICKSTART.md** ← START HERE
**Length:** 5-10 min read
**Purpose:** Executive summary + key decisions
**Contains:**
- Problem & solution overview
- 4-layer architecture diagram
- Essential database schema
- Deployment options
- Common patterns
- Monitoring setup

**Read this if:** You want to understand the approach quickly and see if it fits your needs.

---

### 2. **CONTENT_INGESTION_ARCHITECTURE.md** ← DETAILED REFERENCE
**Length:** 30-45 min read
**Purpose:** Complete technical specification
**Contains:**
- Section 1: Feed aggregation (RSS/Atom/YouTube/Substack/Podcasts)
- Section 2: Scheduling & background jobs (tokio-cron-scheduler)
- Section 3: Change detection & deduplication
- Section 4: Subscription storage & management
- Section 5: Concurrent processing & rate limiting
- Section 6: Complete data pipeline architecture
- Section 7: Long-term operations & deployment
- Section 8: Tech stack summary
- Section 9: Implementation checklist
- Section 10: Design decision explanations
- Section 11: Resources & references

**Read this if:** You're implementing the architecture and need detailed guidance.

---

### 3. **CRATE_RECOMMENDATIONS.md** ← IMPLEMENTATION CHECKLIST
**Length:** 5-10 min read
**Purpose:** Exactly what to add to Cargo.toml
**Contains:**
- Priority 1 crates (core stack)
- Priority 2 crates (source-specific)
- Priority 3 crates (monitoring/operations)
- What NOT to use and why
- Optional enhancements
- Common import patterns
- Crate version tracking
- Size budget

**Read this if:** You're ready to start coding and want to know exactly which crates to add.

---

### 4. **INGESTION_CODE_PATTERNS.md** ← IMPLEMENTATION SKELETON
**Length:** 20-30 min read
**Purpose:** Copy-paste ready code examples
**Contains:**
- Database schema (SQL)
- Rust models & database access layer
- Feed fetching with resilience
- Worker pool implementation
- Cron scheduler setup
- Main application skeleton
- CLI commands for management
- Testing patterns

**Read this if:** You're ready to code and want working examples for each component.

---

## Quick Navigation by Topic

### If you're asking...

**"What crates do I need?"**
→ Start with `CRATE_RECOMMENDATIONS.md`

**"How should I design the database?"**
→ See Section 4 in `CONTENT_INGESTION_ARCHITECTURE.md` OR `INGESTION_CODE_PATTERNS.md` Section 1

**"How do I handle YouTube subscriptions?"**
→ See Section 1.2 in `CONTENT_INGESTION_ARCHITECTURE.md`

**"How do I schedule recurring fetches?"**
→ See Section 2 in `CONTENT_INGESTION_ARCHITECTURE.md` OR `INGESTION_CODE_PATTERNS.md` Section 4

**"How do I prevent rate-limiting bans?"**
→ See Section 5 in `CONTENT_INGESTION_ARCHITECTURE.md`

**"How do I deploy this as a daemon?"**
→ See Section 7 in `CONTENT_INGESTION_ARCHITECTURE.md`

**"How do I detect when content is new/changed?"**
→ See Section 3 in `CONTENT_INGESTION_ARCHITECTURE.md`

**"Where's the complete code example?"**
→ See `INGESTION_CODE_PATTERNS.md`

**"What about Substack, Podcasts, Bluesky?"**
→ See Sections 1.3, 1.4, 1.5 in `CONTENT_INGESTION_ARCHITECTURE.md`

---

## Implementation Path

### Week 1: Foundation
1. Read: `INGESTION_QUICKSTART.md` (understand the approach)
2. Read: `CRATE_RECOMMENDATIONS.md` (decide what to add)
3. Add crates to Cargo.toml
4. Read: `INGESTION_CODE_PATTERNS.md` Section 1 (database)
5. Implement: Database schema + basic models

### Week 2: Fetching & Scheduling
1. Read: `CONTENT_INGESTION_ARCHITECTURE.md` Section 1-2
2. Read: `INGESTION_CODE_PATTERNS.md` Sections 2-4
3. Implement: FeedFetcher with retry logic
4. Implement: IngestionScheduler with cron

### Week 3: Concurrency & Production
1. Read: `CONTENT_INGESTION_ARCHITECTURE.md` Section 5-6
2. Read: `INGESTION_CODE_PATTERNS.md` Section 3
3. Implement: WorkerPool with rate limiting
4. Implement: Main daemon loop

### Week 4: Deployment & Monitoring
1. Read: `CONTENT_INGESTION_ARCHITECTURE.md` Section 7
2. Implement: Daemon setup (systemd/launchd)
3. Implement: Health check endpoint
4. Test end-to-end

---

## Key Architectural Decisions

| Decision | What | Why |
|----------|------|-----|
| **Feed Parser** | `feed-rs` | Unified API for RSS/Atom/JSON Feed |
| **Scheduler** | `tokio-cron-scheduler` | Full cron expressions, timezone aware |
| **Resilience** | `backoff` + `governor` | Exponential retry + rate limiting per domain |
| **Storage** | SQLite (rusqlite) | Single file, ACID, no external dependency |
| **Concurrency** | Semaphore (max 5) | Limits local resource usage |
| **Worker Model** | Tokio tasks + channels | Async-native, handles thousands of items |
| **YouTube** | yt-dlp wrapper + RSS | Official API too expensive |
| **Substack** | RSS only | No public API, just feed URLs |
| **Podcasts** | feed-rs + Podcast Index API | RSS standard, discovery via API |
| **Twitter/X** | Skip | API too expensive, use Bluesky/Mastodon instead |

---

## Sources & References

All recommendations backed by 2026 research on:

- [feed-rs crate](https://docs.rs/feed-rs/latest/feed_rs/) – RSS/Atom/JSON Feed parsing
- [tokio-cron-scheduler](https://docs.rs/tokio-cron-scheduler/latest/tokio_cron_scheduler/) – Cron scheduling
- [Building scalable ingestion pipelines](https://tarkalabs.com/blogs/building-scalable-ingestion-pipeline-rust/)
- [Rate limiting in Rust](https://oneuptime.com/blog/post/2026-01-07-rust-rate-limiting/)
- [Exponential backoff strategies](https://oneuptime.com/blog/post/2026-01-07-rust-retry-exponential-backoff/)
- [yt-dlp wrapper crate](https://github.com/narrrl/ytd-rs)
- [Substack RSS feeds](https://support.substack.com/hc/en-us/articles/360038239391-Is-there-an-RSS-feed-for-my-publication)
- [Podcast Index API](https://podcastindex-org.github.io/docs-api/)
- [systemd service management](https://man.archlinux.org/man/systemd.service.5.en)
- [macOS launchd configuration](https://launchd.info/)

---

## File Sizes

| Document | Lines | Size | Time to Read |
|----------|-------|------|--------------|
| INGESTION_QUICKSTART.md | ~480 | 18 KB | 5-10 min |
| CONTENT_INGESTION_ARCHITECTURE.md | 1,526 | 85 KB | 30-45 min |
| CRATE_RECOMMENDATIONS.md | 192 | 9 KB | 5-10 min |
| INGESTION_CODE_PATTERNS.md | 815 | 42 KB | 20-30 min |
| **Total** | **3,013** | **154 KB** | **60-95 min** |

---

## How to Use This Package

### For Project Managers
Read: `INGESTION_QUICKSTART.md`
Estimated time: 5 minutes

### For Architects
Read: `CONTENT_INGESTION_ARCHITECTURE.md` (all sections)
Reference: `CRATE_RECOMMENDATIONS.md`
Estimated time: 45 minutes

### For Implementers
Read: `CRATE_RECOMMENDATIONS.md`
Reference: `INGESTION_CODE_PATTERNS.md`
Implement: Following the code examples
Estimated time: 3-4 weeks (with other work)

### For Code Reviewers
Reference: `CONTENT_INGESTION_ARCHITECTURE.md` Section 10 (design decisions)
Check: Implementation against `INGESTION_CODE_PATTERNS.md`
Verify: No shortcuts on resilience/rate limiting

---

## What This Research Covers

✅ Feed aggregation (RSS, Atom, JSON Feed)
✅ YouTube channel subscriptions
✅ Substack newsletter integration
✅ Podcast discovery & RSS parsing
✅ Twitter/X alternatives (Bluesky recommendation)
✅ Scheduling & background jobs
✅ Change detection & deduplication
✅ Subscription storage & management
✅ Concurrent processing patterns
✅ Rate limiting strategies
✅ Error handling & resilience
✅ Database design (SQLite)
✅ Data pipeline architecture
✅ Daemon deployment (systemd/launchd)
✅ Health monitoring & observability
✅ Resource usage constraints
✅ Testing patterns

---

## What This Research Does NOT Cover

❌ Web scraping (focus: feed-based sources only)
❌ Machine learning for categorization (out of scope)
❌ Full-text search indexing (separate concern)
❌ API authentication (basic pattern only)
❌ Distributed systems (single-machine focus)
❌ Cloud deployment (self-hosted focus)

---

## Next Steps After Reading

1. **Decision Meeting:** Review architecture with team
2. **Spike:** Try fetching a feed with `feed-rs` (2-3 hours)
3. **Prototype:** Build basic scheduler + worker pool (1 week)
4. **Review:** Get feedback before full implementation
5. **Deploy:** Set up as daemon on development machine
6. **Refine:** Monitor, tune concurrency, add missing sources

---

## Questions During Implementation?

Refer back to:
- **"How does X work?"** → `CONTENT_INGESTION_ARCHITECTURE.md`
- **"What code do I write?"** → `INGESTION_CODE_PATTERNS.md`
- **"Which crate for Y?"** → `CRATE_RECOMMENDATIONS.md`
- **"Why did we choose Z?"** → `CONTENT_INGESTION_ARCHITECTURE.md` Section 10

---

## Version Info

- **Research Date:** 2026-02-01
- **Rust Edition:** 2024 (current in wve-rs)
- **Tokio Version:** 1.40+
- **feed-rs Version:** 0.13+
- **tokio-cron-scheduler Version:** 0.10+

All recommendations are forward-compatible with future Rust versions.

---

## Feedback & Updates

If during implementation you find:
- A crate version incompatibility
- A pattern that doesn't work as documented
- A better approach than recommended

Document it and create a follow-up research issue. Architecture is living documentation.

---

**Ready to build? Start with `INGESTION_QUICKSTART.md` →**
