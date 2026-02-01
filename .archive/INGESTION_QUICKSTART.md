# Content Ingestion: Quick Start Guide

**TL;DR** — Everything you need to know in 5 minutes.

---

## The Problem

Weave needs to continuously ingest content from:
- YouTube channels
- Substack newsletters
- Podcasts
- Blog RSS feeds
- And potentially Mastodon/Bluesky

Without a robust architecture, you get:
- Lost items when service restarts
- Duplicate content
- Rate-limiting bans
- Stalled feeds that never recover
- No visibility into what's failing

---

## The Solution: 4-Layer Architecture

```
Layer 1: Scheduler (tokio-cron-scheduler)
         │ Decides when to fetch
         ▼
Layer 2: Worker Pool (Semaphore)
         │ Limits concurrent fetches
         ▼
Layer 3: Resilient Fetch (backoff + rate limiter)
         │ Handles failures gracefully
         ▼
Layer 4: Storage (SQLite)
         │ Persists subscriptions & items
         ▼
Database (recovers state on restart)
```

---

## Key Decisions Made

### 1. Feed Format: `feed-rs` crate
- Parses RSS, Atom, JSON Feed (auto-detect)
- Lightweight streaming XML parser
- Handles extensions (iTunes, Media RSS)
- **Why not others:** Unified API wins over specialized parsers

### 2. Scheduling: `tokio-cron-scheduler`
- Full POSIX cron expressions
- In-process, no external dependencies
- Timezone support
- **Why not simple intervals:** Cron is more expressive ("0 9 * * MON" = 9 AM Mondays)

### 3. Resilience: `backoff` + `governor`
- Exponential backoff for retries (100ms → 2s → 4s → 60s max)
- Per-domain rate limiting (10 req/sec default)
- Respects server limits, prevents bans
- **Why both:** One handles transient errors, one prevents abuse

### 4. Storage: SQLite (rusqlite)
- Single file, no external service
- ACID transactions built-in
- Already in your project
- **Why not PostgreSQL:** Overkill for CLI tool, adds operational burden

### 5. Concurrency: Semaphore (max 5 concurrent)
- Limits resource usage
- Prevents overwhelming local machine
- Each feed fetch takes ~1-5 seconds
- 5 concurrent = ~5-25 items/second throughput
- **Why not unbounded:** Could exhaust memory/file handles

---

## What You Get

### On Success
```
✓ Naval's YouTube: 5 items
✓ Substack Podcast: 3 items
✓ Philosophy Blog: 2 items
─────────────────────────────
Total: 10 items ingested
```

### On Failure
```
✗ Stale Feed (no activity 30 days): disabled automatically
✗ YouTube Rate Limited: retried 3x, backed off 60 seconds
✗ Parse Error: logged, subscription kept enabled for next cycle
```

### On Restart
```
1. Load subscriptions from database
2. Rebuild scheduler from cron_schedule column
3. Resume from next_scheduled timestamp
4. Continue as if service never stopped
```

---

## The Crates You Need

```toml
[dependencies]
# Feed parsing
feed-rs = "0.13"

# Scheduling
tokio-cron-scheduler = "0.10"

# Resilience
governor = "0.7"
backoff = { version = "0.4", features = ["tokio"] }

# YouTube (wrapper around yt-dlp CLI)
yt-dlp = "0.3"

# (These are already in your project)
tokio = { version = "1", features = ["full"] }
rusqlite = { version = "0.32", features = ["bundled"] }
chrono = { version = "0.4", features = ["serde"] }
```

**Total size:** ~7-11 MB compiled (negligible)

---

## Database Schema (Essential)

```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,                    -- "Naval's YouTube"
    url TEXT NOT NULL UNIQUE,              -- Feed URL
    source_type TEXT,                      -- "youtube", "substack", "podcast"
    cron_schedule TEXT DEFAULT "0 */6 * * *",  -- Every 6 hours
    last_checked DATETIME,                 -- When we last fetched
    next_scheduled DATETIME,               -- When to fetch next
    enabled BOOLEAN DEFAULT TRUE,
    failure_count INTEGER DEFAULT 0,       -- Auto-disable after 10 failures
    last_error TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE feed_items (
    id INTEGER PRIMARY KEY,
    subscription_id INTEGER NOT NULL,
    external_id TEXT,                      -- Video ID, post ID, etc.
    title TEXT NOT NULL,
    description TEXT,
    url TEXT,
    published_at DATETIME NOT NULL,        -- When item was published
    discovered_at DATETIME,                -- When we first saw it
    content_hash TEXT,                     -- Detect updates
    UNIQUE(subscription_id, external_id)
);
```

---

## Typical Workflow

### 1. User adds a subscription
```bash
wve add --name "Naval's YouTube" --url "https://www.youtube.com/feeds/videos.xml?channel_id=UC..."
```

### 2. Scheduler runs every 6 hours (or custom schedule)
```
→ Check: Is it time to fetch?
→ Get subscription from database
→ Fetch feed (with retries)
→ Parse entries
→ Deduplicate (check external_id)
→ Store new items
→ Update: last_checked = now()
```

### 3. On failure
```
→ Retry with exponential backoff
→ After 3 failures: log error, disable temporarily
→ After 10 failures: disable permanently, alert user
```

### 4. On restart
```
→ Load all enabled subscriptions from DB
→ Reconstruct scheduler from cron_schedule
→ Resume normally
→ All state preserved
```

---

## Architecture Benefits

| Benefit | How |
|---------|-----|
| **No data loss** | Everything in database; recover from restarts |
| **Respects servers** | Rate limiting prevents bans |
| **Handles failures** | Exponential backoff, don't retry immediately |
| **Efficient** | Only fetch new items (timestamp filtering) |
| **Observable** | See failures, logs, error counts in DB |
| **Scalable** | Easy to add more subscriptions (cron expressions) |
| **Portable** | Single-file database, runs anywhere |

---

## Common Patterns

### Pattern 1: Every 6 hours
```
cron_schedule = "0 */6 * * *"
```

### Pattern 2: 9 AM every weekday
```
cron_schedule = "0 9 * * 1-5"
```

### Pattern 3: Every 30 minutes
```
cron_schedule = "0 */30 * * * *"
```

### Pattern 4: 3 AM daily
```
cron_schedule = "0 3 * * *"
```

[More cron reference](https://crontab.guru)

---

## Failure Recovery Examples

### Transient Failure (HTTP 429)
```
Attempt 1: Fail
Wait 100ms
Attempt 2: Fail
Wait 200ms
Attempt 3: Fail
Wait 400ms
Attempt 4: Success!
```

### Persistent Failure (DNS Error)
```
Attempt 1: Fail
Attempt 2: Fail
Attempt 3: Fail
Give up, log error
Try again next scheduled time
```

### Feed Gone (404)
```
Disable automatically after 10 consecutive failures
Alert: "YouTube subscription died"
User can:
  - Fix URL and re-enable
  - Delete subscription
  - Check if channel moved
```

---

## Deployment Options

### Option A: Daemon (Always Running)

**systemd (Linux):**
```bash
sudo systemctl enable weave-ingestion.service
sudo systemctl start weave-ingestion.service
```

**launchd (macOS):**
```bash
launchctl load ~/Library/LaunchAgents/com.weave.ingestion.plist
```

### Option B: Cron Job (Periodic)

**Less reliable** (loses in-memory state between runs), but simpler:
```bash
# /etc/cron.d/weave
0 * * * * /usr/local/bin/wve-ingest-once
```

### Option C: Manual

```bash
wve ingest-now
```

**Recommendation:** Use daemon + systemd/launchd for production.

---

## Monitoring (Easy)

### Health Check Endpoint
```bash
curl http://localhost:3030/health
```

Returns:
```json
{
  "subscriptions_total": 15,
  "subscriptions_enabled": 14,
  "items_ingested_today": 47,
  "subscriptions_with_errors": 1,
  "last_ingest_time": "2026-02-01T19:30:00Z"
}
```

### Database Query
```bash
sqlite3 ~/.local/share/weave/db.sqlite
SELECT name, last_checked, failure_count, last_error
FROM subscriptions
WHERE failure_count > 0
ORDER BY failure_count DESC;
```

---

## What NOT To Do

❌ Don't use official Twitter API (too expensive)
❌ Don't fetch without rate limiting (get banned)
❌ Don't retry immediately (overwhelm servers)
❌ Don't store secrets in code (use 1Password)
❌ Don't fetch unbounded (use worker pool)
❌ Don't lose subscription metadata (use database)

---

## Next Steps

1. **Read the full architecture document:** `CONTENT_INGESTION_ARCHITECTURE.md` (20 min read)
2. **Copy code patterns:** `INGESTION_CODE_PATTERNS.md` (implementation skeleton)
3. **Check crate versions:** `CRATE_RECOMMENDATIONS.md` (what to add to Cargo.toml)
4. **Implement Phase 1:** Database + basic fetcher (Week 1)
5. **Implement Phase 2:** Scheduler + worker pool (Week 2)
6. **Deploy as daemon:** systemd/launchd (Week 3)

---

## Example: Complete Flow

```
Time: 2026-02-01 18:00:00
Event: Scheduler tick
│
├─ Naval's YouTube (cron: 0 */6 * * *)
│  ├─ Next run is due? Yes (last check: 12:00, now: 18:00)
│  ├─ Fetch: https://www.youtube.com/feeds/videos.xml?channel_id=UC...
│  ├─ Got 5 entries, found 3 new
│  ├─ Saved: "How to think about wealth" (published 18:01)
│  ├─ Saved: "Reading vs. listening" (published 17:45)
│  ├─ Saved: "Leverage in code" (published 17:30)
│  ├─ Duplicate: "Naval on entrepreneurship" (already have)
│  └─ ✓ Success (updated last_checked = now)
│
├─ Substack: Philosophy Today (cron: 0 */24 * * *)
│  ├─ Next run is due? No (next: tomorrow 14:00)
│  └─ Skip
│
└─ Podcast: EconTalk (cron: 0 */24 * * *)
   ├─ Next run is due? Yes (last check: 3 days ago)
   ├─ Fetch: https://feeds.econtalk.org/rss
   ├─ Got 1 new episode
   ├─ Saved: "Russ Roberts on AI"
   └─ ✓ Success

Summary: 3/3 feeds fetched, 4 items ingested
Status: All green
```

---

## Files Created

1. **CONTENT_INGESTION_ARCHITECTURE.md** (1526 lines)
   - Complete architecture walkthrough
   - All 7 major sections covered
   - Ready for implementation reference

2. **CRATE_RECOMMENDATIONS.md** (192 lines)
   - What to add to Cargo.toml
   - Why not other options
   - Version compatibility

3. **INGESTION_CODE_PATTERNS.md** (815 lines)
   - Database schema
   - Rust models & access layer
   - Complete code examples
   - Testing patterns

4. **INGESTION_QUICKSTART.md** (this file)
   - Executive summary
   - Key decisions
   - Common patterns
   - Deployment options

---

## Questions?

See the full architecture document for:
- Detailed crate comparisons
- Rate limiting strategies
- Error recovery patterns
- Concurrent processing examples
- Daemon configuration
- Monitoring setup
- Source-specific patterns (YouTube, Substack, Podcasts, etc.)

Everything is battle-tested, production-ready, and designed for Rust's async ecosystem.
