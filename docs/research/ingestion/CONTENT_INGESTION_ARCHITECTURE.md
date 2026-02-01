# Content Ingestion & Subscription Management Architecture
## Comprehensive Research for Rust Implementation

**Status:** Research & Recommendations
**Updated:** 2026-02-01
**Target Project:** Weave (wve)

---

## 1. Feed Aggregation Architecture

### 1.1 RSS/Atom Parsing in Rust

**Recommended Primary Crate: `feed-rs`**

The `feed-rs` crate is the most comprehensive option for unified feed parsing:

- **Supports:** Atom, RSS 2.0, RSS 1.0, JSON Feed
- **Extensions:** iTunes, Dublin Core, Media RSS, Podcast Index
- **Parser:** Uses `quick-xml` for lightweight streaming XML
- **Performance:** Minimizes memory usage, avoids unnecessary clones
- **Features:** Automatic format detection (XML vs. JSON)
- **Serialization:** Full serde support for JSON/TOML interchange

```toml
# Cargo.toml
feed-rs = "0.13"  # Latest version
quick-xml = "0.31"  # Used internally
tokio = { version = "1", features = ["full"] }
```

**Architecture Pattern:**
```rust
// Example: Unified feed ingestion
pub struct FeedIngester {
    http_client: reqwest::Client,
    db: Database,
}

impl FeedIngester {
    pub async fn fetch_feed(&self, url: &str) -> Result<feed_rs::model::Feed> {
        let body = self.http_client.get(url).send().await?.text().await?;
        // Automatic format detection
        let feed = feed_rs::parser::parse(body.as_bytes())?;
        Ok(feed)
    }
}
```

**Alternative Options:**
- **`rss` crate** – Specialized for RSS only, lightweight
- **`rss-parser` crate** – Async streaming from any source (files, TCP, HTTP)
- **`atom_syndication`** – Atom-focused, if you only need Atom feeds

**Recommendation:** Use `feed-rs` as primary with fallback to `rss-parser` for streaming scenarios where feed sizes are huge.

---

### 1.2 YouTube Channel Subscriptions

**Architecture: yt-dlp Wrapper + RSS Feeds**

YouTube's official API is expensive ($100/month, 7-day history limit). Better approach:

#### 1.2.1 Channel RSS Discovery

Every YouTube channel has a hidden RSS feed:
```
https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}
```

**How to get channel ID:**
```bash
yt-dlp --print channel_id "https://youtube.com/@channelhandle"
```

**Rust Wrapper Pattern:**
```rust
use yt_dlp::YoutubeDl;

pub struct YouTubeChannelMonitor {
    yt_dlp: YoutubeDl,
}

impl YouTubeChannelMonitor {
    pub async fn get_channel_id(&self, url: &str) -> Result<String> {
        let output = self.yt_dlp
            .format("%(channel_id)s")
            .fetch_info(url)
            .await?;
        Ok(output.stdout.trim().to_string())
    }

    pub fn get_rss_feed(&self, channel_id: &str) -> String {
        format!("https://www.youtube.com/feeds/videos.xml?channel_id={}", channel_id)
    }
}
```

**Crates:**
- **`yt-dlp`** – Async Rust wrapper around yt-dlp CLI (recommended)
- **`youtube-dl-rs`** – Alternative, also wraps yt-dlp with JSON parsing

**Recommended Crate:** `yt-dlp` 0.3.0+ (async-first, plays well with Tokio)

---

### 1.3 Substack Newsletter Subscriptions

**Status:** RSS Only (No Public API)

Substack automatically generates RSS feeds:

```
https://{publication}.substack.com/feed
```

**Important Limitations:**
- Paywalled posts: only headers visible in RSS, not full content
- Requires authentication if you have a subscription
- RSS 2.0 with draft content extension (some readers don't support)

**Architecture Pattern:**
```rust
pub struct SubstackFeedMonitor {
    http_client: reqwest::Client,
    parser: feed_rs::parser::Parse,
}

impl SubstackFeedMonitor {
    pub async fn fetch_newsletter(&self, publication: &str) -> Result<Feed> {
        let url = format!("https://{}.substack.com/feed", publication);
        let body = self.http_client.get(&url).send().await?.text().await?;

        // Use feed-rs for parsing
        let feed = feed_rs::parser::parse(body.as_bytes())?;
        Ok(feed)
    }
}
```

**Third-Party Solutions:**
- **Substack Feed API** (TypeScript-based) – Parses Substack feeds to JSON
- **RSS-Bridge** – Converts various services to RSS (includes Substack)

**Recommendation:** Use standard RSS feed URLs. If you need paywall content, require user authentication or store credentials securely (via 1Password CLI).

---

### 1.4 Twitter/X Alternatives

**Status:** Official API Too Expensive ($100/month, limited scope)

**Recommended Alternative: Bluesky**

Bluesky offers:
- **AT Protocol** (decentralized, open standards)
- **Free tier** with reasonable rate limits
- **RSS-compatible feeds** for public timelines
- **Chronological, user-controlled feeds**

**Architecture:**

```rust
// Bluesky Feed Monitoring
pub struct BlueskyFeedMonitor {
    http_client: reqwest::Client,
    handle: String,  // user handle
}

impl BlueskyFeedMonitor {
    pub async fn fetch_timeline(&self) -> Result<Vec<Post>> {
        // Bluesky AT Protocol endpoint
        let url = format!(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor={}",
            self.handle
        );
        let resp = self.http_client.get(&url).send().await?;
        let posts = resp.json::<Timeline>().await?;
        Ok(posts.feed)
    }
}
```

**Other Alternatives:**
- **Mastodon** – Open-source, decentralized, RSS feeds available
- **Threads** – Meta's Twitter alternative, no official API yet
- **Gab** – RSS feeds available

**Recommendation for Weave:**
If monitoring sources that also post to social media:
1. Prefer direct RSS feeds from personal websites/substacks
2. Fall back to Bluesky for public figures active there
3. Skip X/Twitter unless user specifically provides URL

**Why:** Saves API costs, respects user privacy, decentralized alternatives are more reliable long-term.

---

### 1.5 Podcast Feed Discovery

**Architecture: Podcast Index + RSS**

**Key Insight:** Most podcasts are already RSS-based. Discovery is the challenge.

**Podcast Index:**
- Open-source podcast directory (podcastindex.org)
- ~4 million podcasts indexed
- Free API with rate limits
- Supports search by title, host, topic

**Architecture Pattern:**

```rust
use feed_rs::model::Feed;

pub struct PodcastDiscovery {
    http_client: reqwest::Client,
}

impl PodcastDiscovery {
    /// Search Podcast Index for a podcast
    pub async fn search(&self, query: &str) -> Result<Vec<Podcast>> {
        let url = format!(
            "https://api.podcastindex.org/api/1.0/podcasts/search?q={}",
            urlencoding::encode(query)
        );
        let resp = self.http_client.get(&url).send().await?;
        let results = resp.json::<PodcastSearchResults>().await?;
        Ok(results.feeds)
    }

    /// Fetch podcast RSS feed
    pub async fn fetch_feed(&self, rss_url: &str) -> Result<Feed> {
        let body = self.http_client.get(rss_url).send().await?.text().await?;
        let feed = feed_rs::parser::parse(body.as_bytes())?;
        Ok(feed)
    }

    /// Subscribe to podcast
    pub async fn subscribe(&self, db: &Database, name: &str, rss_url: &str) -> Result<()> {
        let feed = self.fetch_feed(rss_url).await?;
        db.save_subscription(name, rss_url, &feed)?;
        Ok(())
    }
}
```

**Podcast Metadata from Feed:**

```rust
pub struct EpisodeInfo {
    pub title: String,
    pub pub_date: DateTime<Utc>,
    pub duration: Option<Duration>,
    pub transcript_url: Option<String>,  // Some podcasts include
    pub description: String,
}

// Extract from feed-rs Entry
impl From<&feed_rs::model::Entry> for EpisodeInfo {
    fn from(entry: &feed_rs::model::Entry) -> Self {
        Self {
            title: entry.title.as_ref().unwrap_or(&Default::default()).to_string(),
            pub_date: entry.published.unwrap_or_else(Utc::now),
            duration: extract_duration(&entry),
            transcript_url: entry.links
                .iter()
                .find(|l| l.rel == Some("transcript".to_string()))
                .map(|l| l.href.clone()),
            description: entry.summary.as_ref().unwrap_or(&Default::default()).to_string(),
        }
    }
}
```

**Recommendation:**
- Use `feed_rs` for all podcast RSS parsing
- Use Podcast Index API for discovery
- Store subscription metadata in SQLite with `last_checked` timestamp
- Implement incremental polling (only fetch since last check)

---

## 2. Scheduling & Background Jobs

### 2.1 Recommended Approach: `tokio-cron-scheduler`

**Why not just `tokio::time::interval`?**

- `tokio::time::interval` = Fixed durations ("every 5 minutes")
- `tokio-cron-scheduler` = Cron expressions ("0 9 * * *" = 9 AM daily)
- Cron is more expressive and matches user expectations

**Architecture:**

```toml
# Cargo.toml
tokio-cron-scheduler = "0.10"
tokio = { version = "1", features = ["full"] }
chrono = { version = "0.4", features = ["serde"] }
```

**Implementation Pattern:**

```rust
use tokio_cron_scheduler::{Job, JobScheduler};
use std::sync::Arc;

pub struct IngestionScheduler {
    scheduler: JobScheduler,
    ingester: Arc<FeedIngester>,
}

impl IngestionScheduler {
    pub fn new(ingester: Arc<FeedIngester>) -> Result<Self> {
        Ok(Self {
            scheduler: JobScheduler::new()?,
            ingester,
        })
    }

    pub async fn schedule_feeds(&mut self, db: &Database) -> Result<()> {
        let subscriptions = db.get_all_subscriptions()?;

        for sub in subscriptions {
            let ingester = self.ingester.clone();
            let db = db.clone();
            let feed_url = sub.url.clone();

            // Cron expression: "0 */6 * * *" = every 6 hours
            let job = Job::new_async(
                sub.schedule.cron_expression.as_str(),
                move |_, _| {
                    let ingester = ingester.clone();
                    let db = db.clone();
                    let feed_url = feed_url.clone();

                    Box::pin(async move {
                        if let Err(e) = ingester.fetch_and_store(&feed_url, &db).await {
                            eprintln!("Feed fetch error: {}", e);
                        }
                    })
                },
            )?;

            self.scheduler.add(job)?;
        }

        self.scheduler.start().await?;
        Ok(())
    }
}
```

### 2.2 Cron Expression Guide

```
# Format: second minute hour day month weekday
"*/5 * * * * *"         # Every 5 seconds
"0 */5 * * * *"         # Every 5 minutes
"0 0 * * * *"           # Daily at midnight
"0 0 9 * * *"           # Daily at 9 AM
"0 0 * * 0"             # Every Sunday at midnight
"0 0 1 * *"             # First day of month
"0 */6 * * *"           # Every 6 hours (YouTube channels)
"0 0,12 * * *"          # Twice daily (12 AM, 12 PM)
```

### 2.3 Alternative: `schedule` Crate

If you prefer simpler scheduling without cron:

```rust
use schedule::{Agenda, Event};

pub async fn simple_scheduler(ingester: Arc<FeedIngester>, db: Arc<Database>) {
    let mut agenda = Agenda::new();

    // Every 6 hours
    agenda.add(
        Event::interval("Ingest YouTube channels", Duration::from_secs(6 * 3600))
            .callback(move || {
                let ing = ingester.clone();
                let d = db.clone();
                async move {
                    let _ = ing.ingest_all(&d).await;
                }
            })
    );

    agenda.run().await;
}
```

**Comparison:**

| Feature | tokio-cron-scheduler | schedule |
|---------|----------------------|----------|
| Cron expressions | ✅ Full POSIX cron | ❌ No |
| Fixed intervals | ✅ | ✅ |
| Persistence | ❌ In-memory only | ❌ In-memory only |
| Timezone support | ✅ (with `_tz` variants) | ⚠️ Limited |
| Async-native | ✅ Tokio | ✅ Tokio |

**Recommendation:** Use `tokio-cron-scheduler` for maximum expressiveness.

---

### 2.4 Persistence Across Restarts

**Problem:** Scheduler jobs live in memory. Service restarts lose state.

**Solution: Store subscription schedule in database, rebuild at startup**

```rust
// In database schema
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    cron_schedule TEXT NOT NULL,        -- "0 */6 * * *"
    last_checked DATETIME,
    next_scheduled DATETIME,
    failure_count INTEGER DEFAULT 0,
    last_error TEXT,
    enabled BOOLEAN DEFAULT TRUE
);

pub struct Subscription {
    pub id: i64,
    pub name: String,
    pub url: String,
    pub cron_schedule: String,          // Store the expression
    pub last_checked: Option<DateTime<Utc>>,
    pub next_scheduled: Option<DateTime<Utc>>,
    pub failure_count: i32,
    pub enabled: bool,
}
```

**Startup sequence:**
```rust
pub async fn start_scheduler(db: Arc<Database>) -> Result<()> {
    let mut scheduler = IngestionScheduler::new()?;

    // Load all enabled subscriptions from DB
    let subscriptions = db.get_subscriptions_where("enabled = true")?;

    for sub in subscriptions {
        scheduler.schedule_subscription(&sub).await?;

        // Update next_scheduled timestamp
        db.update_subscription(sub.id, UpdateFields {
            next_scheduled: Some(calculate_next_run(&sub.cron_schedule)?),
            ..Default::default()
        })?;
    }

    // Keep scheduler running
    scheduler.start().await?;
    Ok(())
}
```

---

## 3. Change Detection & Incremental Updates

### 3.1 Strategy: Timestamp-Based Incremental Polling

**Core Insight:** Feed items always have publish dates. Track last-checked time.

```rust
pub struct ChangeDetector {
    db: Arc<Database>,
}

impl ChangeDetector {
    pub async fn fetch_new_items(
        &self,
        subscription: &Subscription,
        parser: &FeedParser,
    ) -> Result<Vec<FeedItem>> {
        let feed = parser.fetch(&subscription.url).await?;

        let last_checked = subscription.last_checked.unwrap_or_else(|| {
            Utc::now() - Duration::days(30)  // Default: check last 30 days
        });

        // Filter items published since last check
        let new_items: Vec<_> = feed.entries
            .iter()
            .filter(|entry| {
                entry.published
                    .map(|pub_date| pub_date > last_checked)
                    .unwrap_or(false)
            })
            .map(|entry| FeedItem::from(entry))
            .collect();

        Ok(new_items)
    }
}
```

### 3.2 Deduplication Strategy

**Content-based hashing:**

```rust
use std::collections::HashSet;
use sha2::{Sha256, Digest};

pub fn hash_content(item: &FeedItem) -> String {
    let mut hasher = Sha256::new();

    // Hash: URL + title + published date (not description—can be edited)
    let content = format!(
        "{}{}{}",
        item.url,
        item.title,
        item.published.timestamp()
    );

    hasher.update(content);
    format!("{:x}", hasher.finalize())
}

pub async fn deduplicate_new_items(
    &self,
    subscription_id: i64,
    items: Vec<FeedItem>,
) -> Result<Vec<FeedItem>> {
    // Get hashes of existing items for this subscription
    let existing_hashes: HashSet<String> = self.db
        .get_feed_items_for_subscription(subscription_id)?
        .iter()
        .map(|item| hash_content(&item))
        .collect();

    // Filter out duplicates
    let unique_items = items
        .into_iter()
        .filter(|item| !existing_hashes.contains(&hash_content(item)))
        .collect();

    Ok(unique_items)
}
```

### 3.3 Source URL Versioning

**Track content mutations:**

```rust
#[derive(Clone)]
pub struct FeedItemVersion {
    pub item_id: i64,
    pub url: String,
    pub title: String,
    pub published: DateTime<Utc>,
    pub content_hash: String,
    pub discovered_at: DateTime<Utc>,
}

// When content changes (e.g., blog post updated):
pub async fn handle_content_update(
    &self,
    item_id: i64,
    new_version: FeedItemVersion,
) -> Result<()> {
    let old_version = self.db.get_item_latest_version(item_id)?;

    if old_version.content_hash != new_version.content_hash {
        // Store new version, keep history
        self.db.insert_item_version(new_version)?;

        // Notify subscribers that content was updated
        self.emit_event(Event::ItemUpdated {
            item_id,
            updated_at: Utc::now(),
        }).await?;
    }

    Ok(())
}
```

---

## 4. Subscription Storage & Management

### 4.1 SQLite Schema

```sql
-- Core subscription registry
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identity
    name TEXT NOT NULL,                      -- "Naval's YouTube"
    url TEXT NOT NULL UNIQUE,                -- Feed URL
    source_type TEXT NOT NULL,               -- "youtube", "substack", "podcast", "rss"

    -- Scheduling
    cron_schedule TEXT DEFAULT "0 */6 * * *",  -- Default: every 6 hours
    last_checked DATETIME,
    next_scheduled DATETIME,

    -- Status
    enabled BOOLEAN DEFAULT TRUE,
    failure_count INTEGER DEFAULT 0,
    last_error TEXT,
    last_error_timestamp DATETIME,

    -- Metadata
    description TEXT,
    tags TEXT,                                -- JSON array: ["philosophy", "wealth"]
    category TEXT,
    custom_metadata JSONB,                    -- Store arbitrary data

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Feed items (actual content)
CREATE TABLE feed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,

    -- Content
    external_id TEXT,                        -- YouTube video ID, feed item GUID, etc.
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,                            -- Full HTML/markdown

    -- Metadata
    url TEXT,
    published_at DATETIME NOT NULL,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Version tracking
    content_hash TEXT,                       -- For detecting updates
    version INTEGER DEFAULT 1,

    -- Status
    archived BOOLEAN DEFAULT FALSE,
    read BOOLEAN DEFAULT FALSE,
    tags TEXT,                               -- JSON array for user tagging

    FOREIGN KEY(subscription_id) REFERENCES subscriptions(id),
    UNIQUE(subscription_id, external_id)
);

-- Item version history (track updates)
CREATE TABLE feed_item_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,

    title TEXT,
    description TEXT,
    content TEXT,
    content_hash TEXT,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(item_id) REFERENCES feed_items(id)
);

-- Error tracking for debugging
CREATE TABLE subscription_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,

    error_type TEXT,                        -- "network", "parse", "timeout"
    error_message TEXT,
    error_details JSONB,

    occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,

    FOREIGN KEY(subscription_id) REFERENCES subscriptions(id)
);
```

### 4.2 Rust Models

```rust
use chrono::{DateTime, Utc};
use sqlx::FromRow;

#[derive(Debug, Clone, FromRow)]
pub struct Subscription {
    pub id: i64,
    pub name: String,
    pub url: String,
    pub source_type: String,
    pub cron_schedule: String,
    pub last_checked: Option<DateTime<Utc>>,
    pub next_scheduled: Option<DateTime<Utc>>,
    pub enabled: bool,
    pub failure_count: i32,
    pub last_error: Option<String>,
    pub last_error_timestamp: Option<DateTime<Utc>>,
    pub description: Option<String>,
    pub tags: Option<String>,  // JSON
    pub category: Option<String>,
}

#[derive(Debug, Clone, FromRow)]
pub struct FeedItem {
    pub id: i64,
    pub subscription_id: i64,
    pub external_id: Option<String>,
    pub title: String,
    pub description: Option<String>,
    pub content: Option<String>,
    pub url: Option<String>,
    pub published_at: DateTime<Utc>,
    pub discovered_at: DateTime<Utc>,
    pub content_hash: Option<String>,
    pub version: i32,
    pub archived: bool,
    pub read: bool,
}

impl Subscription {
    pub fn enable(&mut self) {
        self.enabled = true;
        self.failure_count = 0;
        self.last_error = None;
    }

    pub fn disable(&mut self, reason: String) {
        self.enabled = false;
        self.last_error = Some(reason);
    }

    pub fn is_due_for_check(&self) -> bool {
        match self.next_scheduled {
            Some(next) => Utc::now() >= next,
            None => true,
        }
    }
}
```

### 4.3 Tags & Categories

For organizing subscriptions:

```rust
#[derive(Debug, Clone)]
pub enum SourceType {
    YouTube,
    Substack,
    Podcast,
    Blog,
    Twitter,  // For reference only (not recommended)
    Mastodon,
    Bluesky,
    Generic,  // Fallback for unknown RSS
}

impl SourceType {
    pub fn from_str(s: &str) -> Self {
        match s {
            "youtube" => Self::YouTube,
            "substack" => Self::Substack,
            "podcast" => Self::Podcast,
            "blog" => Self::Blog,
            "mastodon" => Self::Mastodon,
            "bluesky" => Self::Bluesky,
            _ => Self::Generic,
        }
    }
}

// Tags stored as JSON array
pub fn parse_tags(json_str: &str) -> Result<Vec<String>> {
    serde_json::from_str(json_str)
        .map_err(|e| anyhow::anyhow!("Failed to parse tags: {}", e))
}

pub fn tags_to_json(tags: &[&str]) -> Result<String> {
    serde_json::to_string(&tags)
        .map_err(|e| anyhow::anyhow!("Failed to serialize tags: {}", e))
}
```

---

## 5. Concurrent Processing & Rate Limiting

### 5.1 Worker Pool Pattern

**Goal:** Process N feeds concurrently without overwhelming servers.

```rust
use tokio::sync::{Semaphore, mpsc};
use std::sync::Arc;

pub struct FeedIngestWorkerPool {
    semaphore: Arc<Semaphore>,           // Max concurrent workers
    db: Arc<Database>,
    http_client: Arc<reqwest::Client>,
}

impl FeedIngestWorkerPool {
    pub fn new(max_concurrent: usize, db: Arc<Database>) -> Self {
        Self {
            semaphore: Arc::new(Semaphore::new(max_concurrent)),
            db,
            http_client: Arc::new(reqwest::Client::new()),
        }
    }

    pub async fn process_all_subscriptions(&self) -> Result<IngestSummary> {
        let subscriptions = self.db.get_enabled_subscriptions()?;

        let mut tasks = vec![];
        let (tx, mut rx) = mpsc::channel(subscriptions.len());

        for sub in subscriptions {
            let permit = self.semaphore.clone();
            let db = self.db.clone();
            let client = self.http_client.clone();
            let tx = tx.clone();

            let task = tokio::spawn(async move {
                let _permit = permit.acquire().await.ok()?;  // Wait for slot

                let result = Self::process_subscription_internal(
                    &sub,
                    &db,
                    &client,
                ).await;

                let _ = tx.send((sub.id, result)).await;  // Report result
                Some(())
            });

            tasks.push(task);
        }

        drop(tx);  // Close sender so receiver knows when done

        // Collect results
        let mut summary = IngestSummary::default();
        while let Some((sub_id, result)) = rx.recv().await {
            match result {
                Ok(items_count) => {
                    summary.success_count += 1;
                    summary.total_items += items_count;
                }
                Err(e) => {
                    summary.failure_count += 1;
                    summary.errors.push((sub_id, e.to_string()));
                }
            }
        }

        Ok(summary)
    }

    async fn process_subscription_internal(
        sub: &Subscription,
        db: &Database,
        client: &reqwest::Client,
    ) -> Result<usize> {
        let feed = Self::fetch_feed(sub, client).await?;
        let items = feed.entries.len();
        db.store_feed_items(sub.id, &feed)?;
        db.update_subscription_checked(sub.id)?;
        Ok(items)
    }

    async fn fetch_feed(sub: &Subscription, client: &reqwest::Client) -> Result<Feed> {
        // With timeout
        let timeout = Duration::from_secs(30);
        let resp = tokio::time::timeout(
            timeout,
            client.get(&sub.url).send()
        ).await
            .map_err(|_| anyhow::anyhow!("Timeout fetching {}", sub.name))?
            .map_err(|e| anyhow::anyhow!("HTTP error: {}", e))?;

        let body = resp.text().await?;
        let feed = feed_rs::parser::parse(body.as_bytes())?;
        Ok(feed)
    }
}

#[derive(Debug, Default)]
pub struct IngestSummary {
    pub success_count: usize,
    pub failure_count: usize,
    pub total_items: usize,
    pub errors: Vec<(i64, String)>,
}
```

**Usage:**
```rust
// In main scheduler
let pool = FeedIngestWorkerPool::new(5, db.clone());  // Max 5 concurrent
let summary = pool.process_all_subscriptions().await?;

eprintln!("Ingestion complete: {} success, {} failures, {} items",
    summary.success_count,
    summary.failure_count,
    summary.total_items
);
```

### 5.2 Rate Limiting with `governor` Crate

**For respecting server limits:**

```toml
governor = "0.7"
```

```rust
use governor::{Quota, RateLimiter};
use nonzero_ext::nonzero;

pub struct RateLimitedFetcher {
    // 10 requests per second per domain
    limiters: Arc<std::sync::Mutex<HashMap<String, RateLimiter>>>,
}

impl RateLimitedFetcher {
    pub fn new() -> Self {
        Self {
            limiters: Arc::new(std::sync::Mutex::new(HashMap::new())),
        }
    }

    pub async fn fetch_with_limit(
        &self,
        url: &str,
        client: &reqwest::Client,
    ) -> Result<String> {
        let domain = extract_domain(url);

        // Get or create limiter for this domain
        let mut limiters = self.limiters.lock().unwrap();
        let limiter = limiters
            .entry(domain.clone())
            .or_insert_with(|| {
                // 10 requests per second
                RateLimiter::direct(Quota::per_second(nonzero!(10u32)))
            });

        // Wait for slot to be available
        limiter.until_ready().await;

        // Fetch
        let resp = client.get(url).send().await?;
        Ok(resp.text().await?)
    }
}
```

### 5.3 Exponential Backoff with `backoff` Crate

**For retrying failed requests:**

```toml
backoff = { version = "0.4", features = ["tokio"] }
```

```rust
use backoff::ExponentialBackoff;
use backoff::future::retry;
use std::time::Duration;

pub async fn fetch_with_retry(
    url: &str,
    client: &reqwest::Client,
) -> Result<String> {
    let backoff = ExponentialBackoff {
        initial_interval: Duration::from_millis(100),
        multiplier: 2.0,
        max_interval: Duration::from_secs(60),
        max_elapsed_time: Some(Duration::from_secs(300)),  // 5 min timeout
        ..Default::default()
    };

    let task = || async {
        client
            .get(url)
            .send()
            .await
            .map_err(backoff::Error::transient)?
            .text()
            .await
            .map_err(backoff::Error::permanent)
    };

    retry(backoff, task).await
}
```

**Backoff strategy for different error types:**

```rust
pub async fn fetch_feed_with_smart_retry(
    sub: &Subscription,
    client: &reqwest::Client,
) -> Result<Feed> {
    let result = fetch_with_retry(&sub.url, client).await;

    match result {
        Ok(body) => {
            feed_rs::parser::parse(body.as_bytes())
                .map_err(|e| anyhow::anyhow!("Parse error: {}", e))
        }
        Err(e) => {
            let error_type = match e.kind() {
                reqwest::error::Kind::Request => "network",
                reqwest::error::Kind::Status => "http_status",
                reqwest::error::Kind::Timeout => "timeout",
                _ => "unknown",
            };

            // Store error for later analysis
            sub.record_error(error_type, &e.to_string())?;

            Err(e)
        }
    }
}
```

---

## 6. Complete Data Pipeline Architecture

### 6.1 High-Level Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     Scheduler Loop (Tokio)                   │
│                                                               │
│  tokio-cron-scheduler checks subscription.cron_schedule      │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│            Feed Ingest Worker Pool (5 concurrent)            │
│                                                               │
│  Semaphore limits concurrent feed fetches                    │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│        Fetch with Rate Limiting & Exponential Backoff        │
│                                                               │
│  governor rate limits per domain                             │
│  backoff retries on transient failures                       │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│           Parse Feed (feed-rs auto-detect format)            │
│                                                               │
│  RSS 1.0 / 2.0 / Atom / JSON Feed                            │
│  Extract extensions (iTunes, Media RSS, etc.)                │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│         Change Detection & Deduplication                     │
│                                                               │
│  Filter: published_at > last_checked                         │
│  Deduplicate: content_hash not in existing items             │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│        Store New Items + Update Subscription Metadata         │
│                                                               │
│  Insert into feed_items table (SQLite)                       │
│  Update subscriptions.last_checked = now()                   │
│  Update subscriptions.next_scheduled = next_cron_time()      │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│              Error Handling & Status Reporting                │
│                                                               │
│  On success: failure_count = 0                               │
│  On transient error: retry with backoff                      │
│  On persistent error: increment failure_count, disable       │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Rust Implementation Skeleton

```rust
// src/ingestion/mod.rs

pub mod scheduler;
pub mod worker_pool;
pub mod feed_parser;
pub mod deduplicator;
pub mod storage;

use std::sync::Arc;
use tokio::time::Duration;

pub struct IngestionPipeline {
    scheduler: scheduler::IngestionScheduler,
    worker_pool: worker_pool::FeedIngestWorkerPool,
    db: Arc<Database>,
}

impl IngestionPipeline {
    pub async fn new(db: Arc<Database>) -> Result<Self> {
        Ok(Self {
            scheduler: scheduler::IngestionScheduler::new()?,
            worker_pool: worker_pool::FeedIngestWorkerPool::new(5, db.clone()),
            db,
        })
    }

    /// Start the ingestion pipeline (blocking)
    pub async fn run(&mut self) -> Result<()> {
        // Load subscriptions from DB
        let subscriptions = self.db.get_enabled_subscriptions()?;

        // Schedule each subscription based on cron expression
        for sub in subscriptions {
            self.scheduler.schedule_subscription(sub).await?;
        }

        // Run scheduler and worker pool concurrently
        let scheduler = self.scheduler.clone();
        let pool = self.worker_pool.clone();
        let db = self.db.clone();

        tokio::select! {
            result = scheduler.run() => {
                eprintln!("Scheduler exited: {:?}", result);
            }
            _ = tokio::signal::ctrl_c() => {
                eprintln!("Received Ctrl-C, shutting down...");
            }
        }

        Ok(())
    }
}

// src/main.rs
#[tokio::main]
async fn main() -> Result<()> {
    let db = Arc::new(Database::new()?);
    let mut pipeline = IngestionPipeline::new(db).await?;

    pipeline.run().await?;

    Ok(())
}
```

---

## 7. Long-term Operations & Deployment

### 7.1 Running as a Daemon

#### Option A: systemd (Linux)

```ini
# /etc/systemd/system/weave-ingestion.service

[Unit]
Description=Weave Content Ingestion Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=weave
WorkingDirectory=/home/weave
ExecStart=/usr/local/bin/wve-ingestion-daemon
Restart=on-failure
RestartSec=10

# Resource limits
MemoryLimit=512M
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable & start:**
```bash
sudo systemctl enable weave-ingestion.service
sudo systemctl start weave-ingestion.service
sudo systemctl status weave-ingestion.service
```

#### Option B: launchd (macOS)

```xml
<!-- ~/Library/LaunchAgents/com.weave.ingestion.plist -->

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.weave.ingestion</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/wve-ingestion-daemon</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/var/log/weave/ingestion.log</string>

    <key>StandardErrorPath</key>
    <string>/var/log/weave/ingestion-error.log</string>

    <key>WorkingDirectory</key>
    <string>/Users/moritzbierling/.local/share/weave</string>
</dict>
</plist>
```

**Load and start:**
```bash
launchctl load ~/Library/LaunchAgents/com.weave.ingestion.plist
launchctl start com.weave.ingestion
launchctl list | grep weave  # Check status
```

### 7.2 Graceful Shutdown

```rust
pub async fn setup_signal_handlers(pipeline: Arc<IngestionPipeline>) {
    let mut sigterm = tokio::signal::unix::signal(
        tokio::signal::unix::SignalKind::terminate()
    ).expect("Failed to setup SIGTERM");

    let mut sigint = tokio::signal::unix::signal(
        tokio::signal::unix::SignalKind::interrupt()
    ).expect("Failed to setup SIGINT");

    tokio::select! {
        _ = sigterm.recv() => {
            eprintln!("Received SIGTERM, gracefully shutting down...");
        }
        _ = sigint.recv() => {
            eprintln!("Received SIGINT, gracefully shutting down...");
        }
    }

    // Wait for in-flight operations to complete
    pipeline.shutdown(Duration::from_secs(30)).await;
}
```

### 7.3 Health Checks & Monitoring

```rust
pub struct HealthChecker {
    db: Arc<Database>,
}

impl HealthChecker {
    pub async fn check(&self) -> HealthStatus {
        HealthStatus {
            uptime: self.get_uptime(),
            subscriptions_total: self.db.count_subscriptions().unwrap_or(0),
            subscriptions_enabled: self.db.count_enabled_subscriptions().unwrap_or(0),
            items_ingested_today: self.db.count_items_since(Duration::from_secs(86400)).unwrap_or(0),
            last_ingest_time: self.db.get_last_ingest_time().ok().flatten(),
            subscriptions_with_errors: self.db.count_subscriptions_with_errors().unwrap_or(0),
            error_details: self.db.get_recent_errors(10).unwrap_or_default(),
        }
    }

    pub async fn serve_http(&self, port: u16) {
        use warp::Filter;

        let health = self.clone();
        let health_route = warp::path("health")
            .map(move || {
                warp::reply::json(&health.check().await)
            });

        warp::serve(health_route).run(([127, 0, 0, 1], port)).await;
    }
}
```

### 7.4 Monitoring Ghost Subscriptions

**Definition:** Subscriptions that haven't received new items in weeks.

```rust
pub async fn check_ghost_subscriptions(db: &Database) -> Result<Vec<GhostSubscription>> {
    let subs = db.get_all_subscriptions()?;
    let stale_threshold = Duration::from_secs(30 * 24 * 3600);  // 30 days

    let mut ghost = vec![];

    for sub in subs {
        if let Some(last_checked) = sub.last_checked {
            let age = Utc::now() - last_checked;

            if age > stale_threshold {
                // Check if there are any items at all
                let item_count = db.count_items_for_subscription(sub.id)?;

                if item_count == 0 {
                    ghost.push(GhostSubscription {
                        subscription: sub,
                        last_activity: last_checked,
                        days_since: age.num_days(),
                        item_count,
                    });
                }
            }
        }
    }

    // Alert if too many ghost subscriptions
    if ghost.len() > 10 {
        eprintln!(
            "WARNING: {} subscriptions have no activity in 30 days",
            ghost.len()
        );
    }

    Ok(ghost)
}
```

### 7.5 Resource Usage Constraints

```rust
pub struct ResourceLimits {
    pub max_memory_bytes: u64,          // 512 MB
    pub max_disk_cache_bytes: u64,      // 1 GB
    pub max_concurrent_workers: usize,  // 5 feeds at once
    pub request_timeout_secs: u64,      // 30 sec per feed
    pub schedule_check_interval: Duration,  // Check cron every 1 min
}

pub async fn monitor_resources(db: Arc<Database>, limits: ResourceLimits) {
    loop {
        // Check memory usage
        let memory_usage = get_process_memory_bytes();
        if memory_usage > limits.max_memory_bytes {
            eprintln!(
                "WARNING: Memory usage ({} MB) exceeds limit ({} MB)",
                memory_usage / 1_000_000,
                limits.max_memory_bytes / 1_000_000
            );

            // Evict old items
            db.delete_items_older_than(Duration::from_days(90)).ok();
        }

        // Check disk usage
        let cache_size = get_cache_dir_size().await;
        if cache_size > limits.max_disk_cache_bytes {
            eprintln!("WARNING: Disk cache exceeds limit, cleaning up...");
            db.optimize_storage().ok();
        }

        tokio::time::sleep(Duration::from_secs(60)).await;
    }
}
```

---

## 8. Recommended Tech Stack Summary

### Core Crates

| Component | Crate | Version | Notes |
|-----------|-------|---------|-------|
| **Feed Parsing** | `feed-rs` | 0.13+ | Unified RSS/Atom/JSON Feed parsing |
| **YouTube** | `yt-dlp` | 0.3+ | Async wrapper around yt-dlp CLI |
| **Scheduling** | `tokio-cron-scheduler` | 0.10+ | Full cron expression support |
| **Async Runtime** | `tokio` | 1.40+ | Full feature set (`features = ["full"]`) |
| **Database** | `rusqlite` | 0.32+ | Already in project, bundled SQLite |
| **HTTP Client** | `reqwest` | 0.12+ | Async, connection pooling |
| **Rate Limiting** | `governor` | 0.7+ | Token bucket rate limiter |
| **Retry Logic** | `backoff` | 0.4+ | Exponential backoff with tokio support |
| **Serialization** | `serde_json` + `toml` | Latest | Already in project |
| **Errors** | `anyhow` + `thiserror` | Latest | Already in project |

### Optional Enhancements

- **`sqlx`** – If moving to async database access (requires migration)
- **`tracing`** – For distributed tracing across async operations
- **`prometheus`** – For metrics collection and monitoring
- **`warp`** – For HTTP health check endpoints
- **`serde_with`** – For custom serialization logic
- **`uuid`** – For generating unique item IDs

---

## 9. Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Add feed aggregation crates to Cargo.toml
- [ ] Design SQLite schema for subscriptions
- [ ] Implement basic feed parsing with `feed-rs`
- [ ] Create subscription CRUD operations
- [ ] Build basic HTTP fetcher with retry logic

### Phase 2: Scheduling (Week 2)
- [ ] Integrate `tokio-cron-scheduler`
- [ ] Implement subscription schedule storage
- [ ] Build subscription load/save from database
- [ ] Test cron expression parsing
- [ ] Setup graceful shutdown handlers

### Phase 3: Pipeline (Week 3)
- [ ] Implement worker pool with semaphore
- [ ] Add rate limiting per domain
- [ ] Build change detection (timestamp + hash)
- [ ] Implement deduplication logic
- [ ] Storage layer for feed items

### Phase 4: Operations (Week 4)
- [ ] Add health check endpoints
- [ ] Implement daemon setup (systemd/launchd)
- [ ] Build monitoring for ghost subscriptions
- [ ] Add resource usage constraints
- [ ] Create admin CLI for subscription management

### Phase 5: Sources (Week 5)
- [ ] YouTube channel RSS discovery
- [ ] Substack feed integration
- [ ] Podcast Index API integration
- [ ] Bluesky API support (optional)
- [ ] Twitter/X scraping note (recommended: skip)

---

## 10. Key Design Decisions Explained

### Why `tokio-cron-scheduler` over simple intervals?

**Answer:** Users think in cron. "Every 6 hours" is easy. "0 9 * * MON" (9 AM on Mondays) is common. Cron expressions are expressive and battle-tested. They also map cleanly to systemd service timers, making it portable.

### Why persistence across restarts matters

**Answer:** A subscription service that loses scheduled tasks on restart is broken by definition. Users set it up once and expect it to keep working. Store all schedule state in the database so recovery is automatic.

### Why incremental polling vs. full refetch?

**Answer:** Incremental saves bandwidth, respects server rate limits, and gives you natural deduplication. Most feeds include publish timestamps; filtering is free. Full refetch only when explicitly needed.

### Why SQLite over external database?

**Answer:** Weave is a CLI tool. Single-file SQLite means:
- No external service dependency
- Easy to ship/backup (`~/.local/share/weave/`)
- ACID transactions built-in
- Scales to thousands of items easily
- Can always migrate to PostgreSQL later

### Why worker pool + rate limiter?

**Answer:**
- **Worker pool** protects local resources (memory, CPU). Prevent 100 feeds from fetching simultaneously.
- **Rate limiter** respects remote servers. YouTube/Substack/etc. have abuse protection.
- Together they balance: fast ingestion without overwhelming servers or client.

---

## 11. Resources & References

### Official Documentation
- [feed-rs docs](https://docs.rs/feed-rs/latest/feed_rs/)
- [tokio-cron-scheduler docs](https://docs.rs/tokio-cron-scheduler/latest/tokio_cron_scheduler/)
- [Tokio tutorial](https://tokio.rs/tokio/tutorial/)
- [Podcast Index API](https://podcastindex-org.github.io/docs-api/)

### Related Reading
- [Scalable Ingestion Pipeline with Rust](https://tarkalabs.com/blogs/building-scalable-ingestion-pipeline-rust/)
- [Building Worker Pools in Rust/Tokio](https://medium.com/@adamszpilewicz/building-a-worker-pool-in-rust-scalable-task-execution-with-tokio-abcb4f193a05)
- [Rate Limiting in Rust](https://oneuptime.com/blog/post/2026-01-07-rust-rate-limiting/view)
- [Exponential Backoff & Retry](https://oneuptime.com/blog/post/2026-01-07-rust-retry-exponential-backoff/view)

### Similar Projects
- **Newsboat** – RSS reader in C++ (good reference for feed scheduling)
- **Miniflux** – Minimalist RSS reader in Go (good data model reference)
- **RSS-Bridge** – Format converter for various services

---

## 12. Next Steps

1. **Create branch:** `feature/content-ingestion-arch`
2. **Add crates to Cargo.toml** (non-breaking)
3. **Design database migrations** (reversible)
4. **Implement Phase 1** (foundation)
5. **Get feedback** before committing to Phase 2+

This research document can be referenced during implementation to maintain consistency with these architectural decisions.
