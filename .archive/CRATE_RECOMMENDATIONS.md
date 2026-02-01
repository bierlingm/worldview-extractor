# Rust Crates for Content Ingestion: Quick Reference

## Priority 1: Core Stack (Add Immediately)

### Feed Aggregation
```toml
feed-rs = "0.13"        # Primary: RSS/Atom/JSON Feed parsing with auto-detection
```
**Why:** Unified API for all feed formats, minimal dependencies, streaming XML parser.

### Scheduling
```toml
tokio-cron-scheduler = "0.10"
tokio = { version = "1", features = ["full"] }
chrono = { version = "0.4", features = ["serde"] }
```
**Why:** Full POSIX cron expressions, timezone support, async-native, in-process persistence.

### HTTP & Resilience
```toml
reqwest = "0.12"        # Already commonly used, use async feature
governor = "0.7"        # Rate limiting per domain
backoff = { version = "0.4", features = ["tokio"] }  # Exponential retry
```

### Database (Already Present)
```toml
rusqlite = { version = "0.32", features = ["bundled"] }  # Keep existing
```

## Priority 2: Source-Specific

### YouTube
```toml
yt-dlp = "0.3"          # Async wrapper around yt-dlp CLI
```
**Alternative:** `youtube-dl-rs` (if you prefer different API)
**Note:** Requires `yt-dlp` CLI installed on system.

### Podcasts
```toml
# feed-rs covers podcast RSS, just need to call Podcast Index API
reqwest = "0.12"        # For Podcast Index REST calls
serde_json = "1"        # Parse API responses
```

## Priority 3: Monitoring & Operations

### Health Checks
```toml
warp = "0.3"            # Lightweight HTTP server for health endpoints
```

### Metrics (Optional)
```toml
prometheus = "0.13"     # If you want Prometheus metrics collection
```

### Logging (Optional, for debugging)
```toml
tracing = "0.1"
tracing-subscriber = "0.3"
```

## Not Recommended (Why)

| What | Why Not |
|------|---------|
| `rustube` for YouTube | Breaks frequently with YouTube changes |
| `tokio::time::interval` alone | Can't express cron schedules |
| `schedule` crate | No cron expressions (only fixed intervals) |
| PostgreSQL/external DB | Overkill for CLI tool, adds operational burden |
| `twitter-api` v2 | Official API too expensive, alternatives limited |
| Custom feed parser | Reinventing wheel, `feed-rs` is battle-tested |

## Optional Enhancements

### Async Database (Future Migration)
```toml
sqlx = { version = "0.8", features = ["sqlite", "tokio-native-tls"] }
```
**When:** If you outgrow rusqlite's synchronous API (rare for CLI tools).

### Structured Logging
```toml
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["json"] }
```
**When:** Running as daemon for production debugging.

### Durable Task Queues (Future)
```toml
sqlx = "0.8"            # Store pending tasks
tokio-util = "0.7"      # Task utilities
```
**When:** If you need task persistence beyond cron (e.g., retries that outlive process restart).

## Common Import Patterns

```rust
// Feed parsing
use feed_rs::parser;
use feed_rs::model::Feed;

// Scheduling
use tokio_cron_scheduler::{Job, JobScheduler};

// HTTP with retry
use reqwest::Client;
use backoff::future::retry;
use backoff::ExponentialBackoff;

// Rate limiting
use governor::RateLimiter;

// Concurrency
use tokio::sync::Semaphore;
use std::sync::Arc;

// Database
use rusqlite::Connection;

// Error handling
use anyhow::{Result, anyhow};
```

## Crate Versions to Watch

- **tokio** – Patches every few weeks, always safe to upgrade
- **feed-rs** – Stable, rarely breaks existing code
- **tokio-cron-scheduler** – Active maintenance, small feature set
- **governor** – Stable rate limiting implementation
- **backoff** – Well-tested, minimal churn

## Size Budget

Current Cargo.toml footprint:
- **feed-rs**: ~3-5 MB compiled
- **tokio-cron-scheduler**: ~2-3 MB compiled
- **governor**: ~1-2 MB compiled
- **backoff**: <1 MB compiled

Total addition: ~7-11 MB (negligible for modern systems).

## Testing These Crates

```bash
# Quick validation script
cargo add feed-rs tokio-cron-scheduler governor backoff

# Test feed parsing
cargo test --lib feed_parsing

# Test scheduling
cargo test --lib scheduler

# Build binary
cargo build --release
```

## Migration Path (If Switching Databases)

```
rusqlite (now)
    ↓
sqlx + sqlite (if async needed, minimal changes)
    ↓
PostgreSQL (only if running server with 100+ concurrent users)
```

For Weave's use case (CLI + personal ingestion), rusqlite is sufficient forever.

## Final Recommendation

**Add these to Cargo.toml immediately:**

```toml
# Feed aggregation
feed-rs = "0.13"

# Scheduling & async
tokio-cron-scheduler = "0.10"

# HTTP & resilience
governor = "0.7"
backoff = { version = "0.4", features = ["tokio"] }

# YouTube
yt-dlp = "0.3"
```

**Total:** 4 crates, battle-tested, minimal maintenance burden, future-proof architecture.
