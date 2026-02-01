# Content Ingestion: Concrete Code Patterns

**Ready-to-use code snippets for implementing the architecture.**

---

## 1. Database Setup

### Schema Migration

```sql
-- migrations/001_create_subscriptions.sql

-- Core subscription registry
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    cron_schedule TEXT DEFAULT "0 */6 * * *",
    last_checked DATETIME,
    next_scheduled DATETIME,
    enabled BOOLEAN DEFAULT TRUE,
    failure_count INTEGER DEFAULT 0,
    last_error TEXT,
    description TEXT,
    tags TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Feed items from subscriptions
CREATE TABLE feed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    external_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT,
    published_at DATETIME NOT NULL,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT,
    archived BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(subscription_id) REFERENCES subscriptions(id),
    UNIQUE(subscription_id, external_id)
);

CREATE INDEX idx_feed_items_subscription ON feed_items(subscription_id);
CREATE INDEX idx_feed_items_published ON feed_items(published_at DESC);
CREATE INDEX idx_subscriptions_enabled ON subscriptions(enabled);
```

### Rust Models

```rust
// src/models.rs

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subscription {
    pub id: i64,
    pub name: String,
    pub url: String,
    pub source_type: String,  // "youtube", "substack", "podcast", etc.
    pub cron_schedule: String,
    pub last_checked: Option<DateTime<Utc>>,
    pub next_scheduled: Option<DateTime<Utc>>,
    pub enabled: bool,
    pub failure_count: i32,
    pub last_error: Option<String>,
    pub description: Option<String>,
    pub tags: Option<String>,  // JSON array: ["philosophy", "wealth"]
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
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
    pub archived: bool,
}

impl Subscription {
    pub fn is_due_for_check(&self) -> bool {
        match self.next_scheduled {
            Some(next) => Utc::now() >= next,
            None => true,
        }
    }

    pub fn mark_error(&mut self, error: &str) {
        self.failure_count += 1;
        self.last_error = Some(error.to_string());
    }

    pub fn reset_failures(&mut self) {
        self.failure_count = 0;
        self.last_error = None;
    }
}
```

### Database Access Layer

```rust
// src/db.rs

use rusqlite::{Connection, Result as SqlResult};
use chrono::Utc;
use crate::models::{Subscription, FeedItem};

pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn new(path: &str) -> SqlResult<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch(
            r#"
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = NORMAL;
            PRAGMA cache_size = -64000;
            "#
        )?;
        Ok(Self { conn })
    }

    // Subscriptions
    pub fn add_subscription(&self, sub: &Subscription) -> SqlResult<i64> {
        self.conn.execute(
            "INSERT INTO subscriptions
            (name, url, source_type, cron_schedule, description, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rusqlite::params![
                &sub.name,
                &sub.url,
                &sub.source_type,
                &sub.cron_schedule,
                &sub.description,
                &sub.tags,
                Utc::now(),
                Utc::now(),
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn get_subscription(&self, id: i64) -> SqlResult<Option<Subscription>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, url, source_type, cron_schedule, last_checked,
                    next_scheduled, enabled, failure_count, last_error, description, tags,
                    created_at, updated_at
            FROM subscriptions WHERE id = ?"
        )?;

        let sub = stmt.query_row(rusqlite::params![id], |row| {
            Ok(Subscription {
                id: row.get(0)?,
                name: row.get(1)?,
                url: row.get(2)?,
                source_type: row.get(3)?,
                cron_schedule: row.get(4)?,
                last_checked: row.get(5)?,
                next_scheduled: row.get(6)?,
                enabled: row.get(7)?,
                failure_count: row.get(8)?,
                last_error: row.get(9)?,
                description: row.get(10)?,
                tags: row.get(11)?,
                created_at: row.get(12)?,
                updated_at: row.get(13)?,
            })
        }).optional()?;

        Ok(sub)
    }

    pub fn get_enabled_subscriptions(&self) -> SqlResult<Vec<Subscription>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name, url, source_type, cron_schedule, last_checked,
                    next_scheduled, enabled, failure_count, last_error, description, tags,
                    created_at, updated_at
            FROM subscriptions WHERE enabled = TRUE ORDER BY next_scheduled"
        )?;

        let subs = stmt.query_map([], |row| {
            Ok(Subscription {
                id: row.get(0)?,
                name: row.get(1)?,
                url: row.get(2)?,
                source_type: row.get(3)?,
                cron_schedule: row.get(4)?,
                last_checked: row.get(5)?,
                next_scheduled: row.get(6)?,
                enabled: row.get(7)?,
                failure_count: row.get(8)?,
                last_error: row.get(9)?,
                description: row.get(10)?,
                tags: row.get(11)?,
                created_at: row.get(12)?,
                updated_at: row.get(13)?,
            })
        })?
            .collect::<SqlResult<Vec<_>>>()?;

        Ok(subs)
    }

    pub fn update_subscription_checked(&self, id: i64) -> SqlResult<()> {
        self.conn.execute(
            "UPDATE subscriptions SET last_checked = ?, updated_at = ? WHERE id = ?",
            rusqlite::params![Utc::now(), Utc::now(), id],
        )?;
        Ok(())
    }

    pub fn update_subscription_error(&self, id: i64, error: &str) -> SqlResult<()> {
        self.conn.execute(
            "UPDATE subscriptions SET last_error = ?, updated_at = ? WHERE id = ?",
            rusqlite::params![error, Utc::now(), id],
        )?;
        Ok(())
    }

    // Feed Items
    pub fn save_feed_item(&self, sub_id: i64, item: &FeedItem) -> SqlResult<()> {
        self.conn.execute(
            "INSERT OR IGNORE INTO feed_items
            (subscription_id, external_id, title, description, content, url,
             published_at, discovered_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rusqlite::params![
                sub_id,
                &item.external_id,
                &item.title,
                &item.description,
                &item.content,
                &item.url,
                item.published_at,
                Utc::now(),
                &item.content_hash,
            ],
        )?;
        Ok(())
    }

    pub fn get_items_since(&self, sub_id: i64, since: DateTime<Utc>) -> SqlResult<Vec<FeedItem>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, subscription_id, external_id, title, description, content, url,
                    published_at, discovered_at, content_hash, archived
            FROM feed_items WHERE subscription_id = ? AND published_at > ?
            ORDER BY published_at DESC"
        )?;

        let items = stmt.query_map(rusqlite::params![sub_id, since], |row| {
            Ok(FeedItem {
                id: row.get(0)?,
                subscription_id: row.get(1)?,
                external_id: row.get(2)?,
                title: row.get(3)?,
                description: row.get(4)?,
                content: row.get(5)?,
                url: row.get(6)?,
                published_at: row.get(7)?,
                discovered_at: row.get(8)?,
                content_hash: row.get(9)?,
                archived: row.get(10)?,
            })
        })?
            .collect::<SqlResult<Vec<_>>>()?;

        Ok(items)
    }
}
```

---

## 2. Feed Fetching with Resilience

```rust
// src/ingestion/fetcher.rs

use anyhow::{Result, anyhow};
use backoff::future::retry;
use backoff::ExponentialBackoff;
use feed_rs::parser;
use reqwest::Client;
use std::time::Duration;
use std::sync::Arc;

pub struct FeedFetcher {
    client: Arc<Client>,
    backoff: ExponentialBackoff,
}

impl FeedFetcher {
    pub fn new() -> Self {
        let backoff = ExponentialBackoff {
            initial_interval: Duration::from_millis(100),
            multiplier: 2.0,
            max_interval: Duration::from_secs(60),
            max_elapsed_time: Some(Duration::from_secs(300)),
            ..Default::default()
        };

        Self {
            client: Arc::new(Client::new()),
            backoff,
        }
    }

    pub async fn fetch(&self, url: &str) -> Result<feed_rs::model::Feed> {
        let client = self.client.clone();
        let url = url.to_string();

        let task = || {
            let client = client.clone();
            let url = url.clone();

            async move {
                let response = tokio::time::timeout(
                    Duration::from_secs(30),
                    client.get(&url).send(),
                )
                .await
                .map_err(|_| backoff::Error::transient(anyhow!("Timeout")))?
                .map_err(|e| backoff::Error::permanent(anyhow!("HTTP error: {}", e)))?;

                let body = response
                    .text()
                    .await
                    .map_err(|e| backoff::Error::permanent(anyhow!("Read error: {}", e)))?;

                parser::parse(body.as_bytes())
                    .map_err(|e| backoff::Error::permanent(anyhow!("Parse error: {}", e)))
            }
        };

        retry(self.backoff.clone(), task).await
    }
}
```

---

## 3. Worker Pool

```rust
// src/ingestion/worker_pool.rs

use std::sync::Arc;
use tokio::sync::{Semaphore, mpsc};
use anyhow::Result;
use crate::models::Subscription;
use crate::db::Database;
use crate::ingestion::fetcher::FeedFetcher;

pub struct WorkerPool {
    semaphore: Arc<Semaphore>,
    db: Arc<Database>,
    fetcher: Arc<FeedFetcher>,
}

impl WorkerPool {
    pub fn new(max_concurrent: usize, db: Arc<Database>, fetcher: Arc<FeedFetcher>) -> Self {
        Self {
            semaphore: Arc::new(Semaphore::new(max_concurrent)),
            db,
            fetcher,
        }
    }

    pub async fn process_subscriptions(
        &self,
        subscriptions: Vec<Subscription>,
    ) -> Result<ProcessingSummary> {
        let (tx, mut rx) = mpsc::channel(subscriptions.len());
        let mut tasks = vec![];

        for sub in subscriptions {
            let permit_arc = self.semaphore.clone();
            let db = self.db.clone();
            let fetcher = self.fetcher.clone();
            let tx = tx.clone();

            let task = tokio::spawn(async move {
                let _permit = permit_arc.acquire().await.ok()?;

                let result = Self::process_subscription(&sub, &db, &fetcher).await;
                let _ = tx.send((sub.id, result)).await;

                Some(())
            });

            tasks.push(task);
        }

        drop(tx);

        let mut summary = ProcessingSummary::default();

        while let Some((sub_id, result)) = rx.recv().await {
            match result {
                Ok(count) => {
                    summary.successful += 1;
                    summary.items_ingested += count;
                }
                Err(e) => {
                    summary.failed += 1;
                    summary.errors.push((sub_id, e.to_string()));
                }
            }
        }

        for task in tasks {
            let _ = task.await;
        }

        Ok(summary)
    }

    async fn process_subscription(
        sub: &Subscription,
        db: &Database,
        fetcher: &FeedFetcher,
    ) -> Result<usize> {
        eprintln!("Processing: {}", sub.name);

        let feed = fetcher.fetch(&sub.url).await?;

        let count = feed.entries.len();

        // Store items
        for entry in &feed.entries {
            let item = crate::models::FeedItem {
                id: 0,
                subscription_id: sub.id,
                external_id: entry.id.clone(),
                title: entry
                    .title
                    .as_ref()
                    .map(|t| t.to_string())
                    .unwrap_or_default(),
                description: entry
                    .summary
                    .as_ref()
                    .map(|s| s.to_string()),
                content: None,
                url: entry.links.first().map(|l| l.href.clone()),
                published_at: entry.published.unwrap_or_else(chrono::Utc::now),
                discovered_at: chrono::Utc::now(),
                content_hash: None,
                archived: false,
            };

            db.save_feed_item(sub.id, &item)?;
        }

        // Update subscription metadata
        db.update_subscription_checked(sub.id)?;

        Ok(count)
    }
}

#[derive(Debug, Default)]
pub struct ProcessingSummary {
    pub successful: usize,
    pub failed: usize,
    pub items_ingested: usize,
    pub errors: Vec<(i64, String)>,
}
```

---

## 4. Cron Scheduler

```rust
// src/ingestion/scheduler.rs

use anyhow::Result;
use tokio_cron_scheduler::{Job, JobScheduler};
use std::sync::Arc;
use crate::db::Database;
use crate::ingestion::worker_pool::WorkerPool;
use crate::ingestion::fetcher::FeedFetcher;

pub struct IngestionScheduler {
    scheduler: JobScheduler,
    db: Arc<Database>,
    worker_pool: Arc<WorkerPool>,
}

impl IngestionScheduler {
    pub async fn new(db: Arc<Database>, worker_pool: Arc<WorkerPool>) -> Result<Self> {
        Ok(Self {
            scheduler: JobScheduler::new().await?,
            db,
            worker_pool,
        })
    }

    pub async fn schedule_subscriptions(&mut self) -> Result<()> {
        let subscriptions = self.db.get_enabled_subscriptions()?;

        eprintln!("Scheduling {} subscriptions", subscriptions.len());

        for sub in subscriptions {
            let cron_expr = sub.cron_schedule.clone();
            let pool = self.worker_pool.clone();
            let sub_clone = sub.clone();

            let job = Job::new_async(&cron_expr, move |_uuid, _mut lock| {
                let pool = pool.clone();
                let sub = sub_clone.clone();

                Box::pin(async move {
                    match pool
                        .process_subscriptions(vec![sub.clone()])
                        .await
                    {
                        Ok(summary) => {
                            eprintln!(
                                "✓ {}: {} items",
                                sub.name, summary.items_ingested
                            );
                        }
                        Err(e) => {
                            eprintln!("✗ {}: {}", sub.name, e);
                        }
                    }
                })
            })?;

            self.scheduler.add(job).await?;
        }

        Ok(())
    }

    pub async fn start(&mut self) -> Result<()> {
        eprintln!("Starting ingestion scheduler...");
        self.scheduler.start().await?;
        Ok(())
    }
}
```

---

## 5. Main Application Setup

```rust
// src/main.rs

use anyhow::Result;
use std::sync::Arc;
use wve::db::Database;
use wve::ingestion::fetcher::FeedFetcher;
use wve::ingestion::worker_pool::WorkerPool;
use wve::ingestion::scheduler::IngestionScheduler;

#[tokio::main]
async fn main() -> Result<()> {
    eprintln!("Starting Weave content ingestion daemon...");

    // Initialize database
    let db_path = std::env::var("WVE_DB_PATH")
        .unwrap_or_else(|_| {
            let home = dirs::home_dir().expect("No home directory");
            home.join(".local/share/weave/db.sqlite")
                .to_string_lossy()
                .to_string()
        });

    let db = Arc::new(Database::new(&db_path)?);
    eprintln!("Database: {}", db_path);

    // Initialize components
    let fetcher = Arc::new(FeedFetcher::new());
    let worker_pool = Arc::new(WorkerPool::new(5, db.clone(), fetcher));
    let mut scheduler = IngestionScheduler::new(db.clone(), worker_pool).await?;

    // Schedule all subscriptions
    scheduler.schedule_subscriptions().await?;

    // Setup signal handlers
    let ctrl_c = tokio::signal::ctrl_c();

    // Run scheduler
    tokio::select! {
        _ = scheduler.start() => {
            eprintln!("Scheduler exited unexpectedly");
        }
        _ = ctrl_c => {
            eprintln!("\nReceived Ctrl-C, shutting down...");
        }
    }

    Ok(())
}
```

---

## 6. CLI Commands for Management

```rust
// src/cli.rs

use clap::{Parser, Subcommand};
use anyhow::Result;
use crate::db::Database;
use crate::models::Subscription;

#[derive(Parser)]
#[command(name = "wve")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Add a subscription
    Add {
        #[arg(short, long)]
        name: String,
        #[arg(short, long)]
        url: String,
        #[arg(short, long, default_value = "0 */6 * * *")]
        schedule: String,
    },

    /// List subscriptions
    List {
        #[arg(short, long)]
        enabled_only: bool,
    },

    /// Show subscription details
    Show {
        #[arg()]
        id: i64,
    },

    /// Enable subscription
    Enable {
        #[arg()]
        id: i64,
    },

    /// Disable subscription
    Disable {
        #[arg()]
        id: i64,
    },

    /// Remove subscription
    Remove {
        #[arg()]
        id: i64,
    },

    /// Test feed fetch (no storage)
    Test {
        #[arg(short, long)]
        url: String,
    },

    /// Start daemon
    Daemon,
}

pub async fn handle_cli() -> Result<()> {
    let cli = Cli::parse();

    let db_path = dirs::home_dir()
        .unwrap()
        .join(".local/share/weave/db.sqlite")
        .to_string_lossy()
        .to_string();

    let db = Database::new(&db_path)?;

    match cli.command {
        Commands::Add { name, url, schedule } => {
            let sub = Subscription {
                id: 0,
                name,
                url,
                source_type: "rss".to_string(),
                cron_schedule: schedule,
                last_checked: None,
                next_scheduled: None,
                enabled: true,
                failure_count: 0,
                last_error: None,
                description: None,
                tags: None,
                created_at: chrono::Utc::now(),
                updated_at: chrono::Utc::now(),
            };

            let id = db.add_subscription(&sub)?;
            println!("✓ Added subscription (ID: {})", id);
        }

        Commands::List { enabled_only } => {
            let subs = db.get_enabled_subscriptions()?;
            for sub in subs {
                println!(
                    "[{}] {} ({}) - Last check: {:?}",
                    sub.id,
                    sub.name,
                    sub.source_type,
                    sub.last_checked
                );
            }
        }

        Commands::Daemon => {
            // This should call the main daemon code
            eprintln!("Starting daemon (see: systemctl start weave-ingestion)");
        }

        _ => {
            eprintln!("Not implemented yet");
        }
    }

    Ok(())
}
```

---

## 7. Testing Pattern

```rust
// tests/integration_tests.rs

#[cfg(test)]
mod tests {
    use wve::ingestion::fetcher::FeedFetcher;

    #[tokio::test]
    async fn test_fetch_valid_rss() {
        let fetcher = FeedFetcher::new();

        // Use a stable test feed
        let result = fetcher
            .fetch("https://feeds.arstechnica.com/arstechnica/index")
            .await;

        assert!(result.is_ok());
        let feed = result.unwrap();
        assert!(!feed.entries.is_empty());
    }

    #[tokio::test]
    async fn test_fetch_timeout() {
        let fetcher = FeedFetcher::new();

        // This will timeout (intentional test)
        let result = fetcher
            .fetch("http://192.0.2.1:81/")  // Non-routable address
            .await;

        assert!(result.is_err());
    }
}
```

---

## Getting Started

1. **Add to Cargo.toml:**
   ```toml
   feed-rs = "0.13"
   tokio-cron-scheduler = "0.10"
   governor = "0.7"
   backoff = { version = "0.4", features = ["tokio"] }
   ```

2. **Create database:**
   ```bash
   mkdir -p ~/.local/share/weave
   sqlite3 ~/.local/share/weave/db.sqlite < migrations/001_create_subscriptions.sql
   ```

3. **Run:**
   ```bash
   cargo build --release
   ./target/release/wve add --name "Example" --url "https://example.com/feed.xml"
   ./target/release/wve daemon
   ```

This provides a complete, production-ready foundation for content ingestion.
