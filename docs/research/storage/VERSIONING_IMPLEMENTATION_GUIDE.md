# Versioning Implementation Guide for Weave

Practical patterns to integrate professional-grade versioning into the Weave codebase.

## Phase 1: Audit Trail (Low-effort, High-value)

### 1.1 Add JSONL Audit Log

**File**: `.wve/store/{slug}/audit.jsonl` (append-only)

```rust
// src/storage/audit.rs (new file)

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEntry {
    pub id: String,
    pub timestamp: DateTime<Utc>,
    pub operation: String,             // "create", "update_points", "update_subject"
    pub user: String,                  // $USER or "cli"
    pub wve_version: String,           // env!("CARGO_PKG_VERSION")
    pub reason: String,                // --reason flag
    pub before: Option<serde_json::Value>,
    pub after: serde_json::Value,
    pub changes: Vec<Change>,
    pub metadata: std::collections::HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Change {
    pub path: String,                  // "/points/0/stance"
    pub op: String,                    // "add", "remove", "replace"
    pub old_value: Option<serde_json::Value>,
    pub new_value: Option<serde_json::Value>,
}

pub fn get_audit_log_path(slug: &str) -> PathBuf {
    let home = dirs::home_dir().expect("Could not find home directory");
    home.join(".wve").join("store").join(slug).join("audit.jsonl")
}

pub fn append_audit_entry(slug: &str, entry: &AuditEntry) -> Result<(), Box<dyn std::error::Error>> {
    let path = get_audit_log_path(slug);

    // Ensure directory exists
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    // Append to JSONL (one JSON per line)
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)?;

    let json_line = serde_json::to_string(&entry)?;
    writeln!(file, "{}", json_line)?;

    Ok(())
}

pub fn get_audit_log(slug: &str) -> Result<Vec<AuditEntry>, Box<dyn std::error::Error>> {
    let path = get_audit_log_path(slug);

    if !path.exists() {
        return Ok(Vec::new());
    }

    let content = std::fs::read_to_string(&path)?;
    let entries = content
        .lines()
        .filter(|line| !line.is_empty())
        .map(|line| serde_json::from_str(line))
        .collect::<Result<Vec<_>, _>>()?;

    Ok(entries)
}

// Compute semantic changes
pub fn compute_changes(before: &crate::models::Worldview, after: &crate::models::Worldview) -> Vec<Change> {
    let mut changes = Vec::new();

    if before.subject != after.subject {
        changes.push(Change {
            path: "/subject".to_string(),
            op: "replace".to_string(),
            old_value: Some(serde_json::Value::String(before.subject.clone())),
            new_value: Some(serde_json::Value::String(after.subject.clone())),
        });
    }

    let before_by_theme: std::collections::HashMap<_, _> = before.points.iter()
        .map(|p| (&p.theme, p))
        .collect();
    let after_by_theme: std::collections::HashMap<_, _> = after.points.iter()
        .map(|p| (&p.theme, p))
        .collect();

    // Removals
    for (theme, old_point) in &before_by_theme {
        if !after_by_theme.contains_key(theme) {
            changes.push(Change {
                path: format!("/points/{}", theme),
                op: "remove".to_string(),
                old_value: Some(serde_json::to_value(old_point).unwrap_or(serde_json::Value::Null)),
                new_value: None,
            });
        }
    }

    // Additions and modifications
    for (theme, new_point) in &after_by_theme {
        if let Some(old_point) = before_by_theme.get(theme) {
            if old_point != &new_point {
                changes.push(Change {
                    path: format!("/points/{}", theme),
                    op: "replace".to_string(),
                    old_value: Some(serde_json::to_value(old_point).unwrap_or(serde_json::Value::Null)),
                    new_value: Some(serde_json::to_value(new_point).unwrap_or(serde_json::Value::Null)),
                });
            }
        } else {
            changes.push(Change {
                path: format!("/points/{}", theme),
                op: "add".to_string(),
                old_value: None,
                new_value: Some(serde_json::to_value(new_point).unwrap_or(serde_json::Value::Null)),
            });
        }
    }

    changes
}
```

### 1.2 Integrate Audit Logging into Save

**Update**: `src/storage/json_store.rs`

```rust
use crate::storage::audit;

pub fn save_worldview(worldview: &Worldview) -> Result<PathBuf, StorageError> {
    let dir = get_worldview_dir(&worldview.slug);
    std::fs::create_dir_all(&dir)?;

    let file_path = dir.join("worldview.json");

    // Load previous version for audit
    let before = load_worldview(&worldview.slug).ok();

    // Write new version
    let json = serde_json::to_string_pretty(worldview)?;
    std::fs::write(&file_path, &json)?;

    // Log audit entry
    if let Ok(before_data) = before {
        let user = std::env::var("USER").unwrap_or_else(|_| "unknown".to_string());
        let reason = std::env::var("WVE_REASON").unwrap_or_else(|_| "Manual edit".to_string());

        let changes = audit::compute_changes(&before_data, worldview);
        let entry = audit::AuditEntry {
            id: uuid::Uuid::new_v4().to_string(),
            timestamp: chrono::Utc::now(),
            operation: "update".to_string(),
            user,
            wve_version: env!("CARGO_PKG_VERSION").to_string(),
            reason,
            before: Some(serde_json::to_value(&before_data)?),
            after: serde_json::to_value(worldview)?,
            changes,
            metadata: Default::default(),
        };

        audit::append_audit_entry(&worldview.slug, &entry)?;
    }

    Ok(file_path)
}
```

### 1.3 View Audit Log (CLI command)

**Update**: `src/cli.rs`

```rust
#[derive(Parser)]
enum Command {
    #[command(about = "View audit history")]
    History {
        #[arg(help = "Worldview slug")]
        slug: String,

        #[arg(short, long, help = "Show last N entries")]
        limit: Option<usize>,

        #[arg(short, long, help = "Output as JSON")]
        json: bool,
    },
    // ... other commands
}

fn handle_history(slug: &str, limit: Option<usize>, json: bool) -> Result<(), Box<dyn std::error::Error>> {
    let entries = crate::storage::audit::get_audit_log(slug)?;

    let entries: Vec<_> = if let Some(n) = limit {
        entries.into_iter().rev().take(n).collect()
    } else {
        entries
    };

    if json {
        println!("{}", serde_json::to_string_pretty(&entries)?);
    } else {
        for entry in entries.iter().rev() {
            println!("{} - {} by {} ({} changes)",
                entry.timestamp,
                entry.operation,
                entry.user,
                entry.changes.len()
            );

            if !entry.reason.is_empty() {
                println!("  Reason: {}", entry.reason);
            }

            for change in &entry.changes {
                println!("    {} {}: {:?} → {:?}",
                    change.op,
                    change.path,
                    change.old_value,
                    change.new_value
                );
            }
            println!();
        }
    }

    Ok(())
}
```

---

## Phase 2: Versioning with Snapshots

### 2.1 Add Versioning Table to SQLite

**Migration**:
```sql
CREATE TABLE IF NOT EXISTS worldview_versions (
    id INTEGER PRIMARY KEY,
    worldview_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    slug TEXT NOT NULL,
    data TEXT NOT NULL,                -- Full JSON snapshot
    created_at TEXT NOT NULL,          -- ISO 8601 timestamp
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    UNIQUE(worldview_id, version),
    FOREIGN KEY(worldview_id) REFERENCES worldviews(id)
);

CREATE INDEX idx_worldview_version ON worldview_versions(worldview_id, version DESC);
CREATE INDEX idx_worldview_created ON worldview_versions(created_at DESC);
```

### 2.2 Version Management Functions

```rust
// src/storage/versioning.rs (new file)

use rusqlite::{Connection, params};
use chrono::{DateTime, Utc};
use crate::models::Worldview;

#[derive(Debug, Clone)]
pub struct VersionInfo {
    pub id: i64,
    pub version: i64,
    pub created_at: DateTime<Utc>,
    pub created_by: String,
    pub reason: String,
}

pub fn save_version(
    conn: &Connection,
    worldview_id: i64,
    slug: &str,
    worldview: &Worldview,
    user: &str,
    reason: &str,
) -> Result<i64, Box<dyn std::error::Error>> {
    // Get next version number
    let next_version: i64 = conn.query_row(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM worldview_versions WHERE worldview_id = ?",
        params![worldview_id],
        |row| row.get(0),
    )?;

    let data = serde_json::to_string(worldview)?;
    let created_at = Utc::now().to_rfc3339();

    conn.execute(
        "INSERT INTO worldview_versions (worldview_id, version, slug, data, created_at, created_by, reason)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        params![
            worldview_id,
            next_version,
            slug,
            data,
            created_at,
            user,
            reason,
        ],
    )?;

    Ok(next_version)
}

pub fn get_version(
    conn: &Connection,
    worldview_id: i64,
    version: i64,
) -> Result<Worldview, Box<dyn std::error::Error>> {
    let data: String = conn.query_row(
        "SELECT data FROM worldview_versions WHERE worldview_id = ? AND version = ?",
        params![worldview_id, version],
        |row| row.get(0),
    )?;

    Ok(serde_json::from_str(&data)?)
}

pub fn list_versions(
    conn: &Connection,
    worldview_id: i64,
) -> Result<Vec<VersionInfo>, Box<dyn std::error::Error>> {
    let mut stmt = conn.prepare(
        "SELECT id, version, created_at, created_by, reason
         FROM worldview_versions
         WHERE worldview_id = ?
         ORDER BY version DESC",
    )?;

    let versions = stmt.query_map(params![worldview_id], |row| {
        Ok(VersionInfo {
            id: row.get(0)?,
            version: row.get(1)?,
            created_at: row.get::<_, String>(2)?.parse().unwrap_or_else(|_| Utc::now()),
            created_by: row.get(3)?,
            reason: row.get(4)?,
        })
    })?;

    let mut results = Vec::new();
    for version in versions {
        results.push(version?);
    }

    Ok(results)
}

pub fn rollback_to_version(
    conn: &Connection,
    worldview_id: i64,
    target_version: i64,
) -> Result<Worldview, Box<dyn std::error::Error>> {
    let worldview = get_version(conn, worldview_id, target_version)?;
    Ok(worldview)
}
```

### 2.3 Add `--version` flag to diff command

```rust
#[derive(Parser)]
enum Command {
    #[command(about = "Show differences between versions")]
    Diff {
        slug: String,

        #[arg(long, help = "Version to compare from")]
        from_version: Option<i64>,

        #[arg(long, help = "Version to compare to")]
        to_version: Option<i64>,

        #[arg(short, long, help = "Output as JSON")]
        json: bool,
    },
}
```

---

## Phase 3: Semantic Diffing with json-patch

### 3.1 Add json-patch dependency

**Update `Cargo.toml`**:
```toml
json-patch = "1.1"
uuid = { version = "1.0", features = ["v4", "serde"] }
```

### 3.2 Unified Diff Display

```rust
// src/comparison/semantic_diff.rs (update existing)

use json_patch::diff;
use serde_json::{json, Value};

pub fn diff_worldviews_semantic(
    old: &crate::models::Worldview,
    new: &crate::models::Worldview,
) -> Result<Value, Box<dyn std::error::Error>> {
    let old_value = serde_json::to_value(old)?;
    let new_value = serde_json::to_value(new)?;

    // Use RFC 6902 JSON Patch
    let patch = diff(&old_value, &new_value);

    Ok(serde_json::Value::Array(
        patch.iter().map(|op| serde_json::to_value(op).unwrap()).collect()
    ))
}

pub fn display_diff_human(old: &crate::models::Worldview, new: &crate::models::Worldview) {
    // Subject change
    if old.subject != new.subject {
        println!("Subject: {} → {}", old.subject, new.subject);
    }

    let old_by_theme: std::collections::HashMap<_, _> = old.points.iter()
        .map(|p| (&p.theme, p))
        .collect();
    let new_by_theme: std::collections::HashMap<_, _> = new.points.iter()
        .map(|p| (&p.theme, p))
        .collect();

    for theme in new_by_theme.keys() {
        if let Some(old_point) = old_by_theme.get(theme) {
            let new_point = &new_by_theme[theme];

            if old_point.stance != new_point.stance {
                println!("  {} stance: {} → {}", theme, old_point.stance, new_point.stance);
            }

            if (old_point.confidence - new_point.confidence).abs() > 0.001 {
                println!("  {} confidence: {:.2} → {:.2}", theme, old_point.confidence, new_point.confidence);
            }
        } else {
            let new_point = &new_by_theme[theme];
            println!("  + {}: {} (confidence: {:.2})", theme, new_point.stance, new_point.confidence);
        }
    }

    for theme in old_by_theme.keys() {
        if !new_by_theme.contains_key(theme) {
            println!("  - {}", theme);
        }
    }
}
```

---

## Phase 4: Three-Way Merge (Optional, for Multi-User)

### 4.1 Add threeway_merge dependency

**Update `Cargo.toml`**:
```toml
threeway_merge = "0.1"
```

### 4.2 Merge Implementation

```rust
// src/synthesis/merge.rs (new file)

use crate::models::Worldview;

pub enum MergeConflict {
    ConflictingStance {
        theme: String,
        base: String,
        yours: String,
        theirs: String,
    },
    ConflictingConfidence {
        theme: String,
        base: f64,
        yours: f64,
        theirs: f64,
    },
}

pub fn merge_worldviews(
    base: &Worldview,
    yours: &Worldview,
    theirs: &Worldview,
) -> Result<(Worldview, Vec<MergeConflict>), Box<dyn std::error::Error>> {
    let mut conflicts = Vec::new();
    let mut merged = base.clone();

    let base_by_theme: std::collections::HashMap<_, _> = base.points.iter()
        .map(|p| (&p.theme, p))
        .collect();
    let yours_by_theme: std::collections::HashMap<_, _> = yours.points.iter()
        .map(|p| (&p.theme, p))
        .collect();
    let theirs_by_theme: std::collections::HashMap<_, _> = theirs.points.iter()
        .map(|p| (&p.theme, p))
        .collect();

    // Merge subject
    if yours.subject != base.subject && theirs.subject != base.subject {
        // Both changed subject (conflict)
        // For now, take yours (last-write-wins)
        merged.subject = yours.subject.clone();
    } else if theirs.subject != base.subject {
        merged.subject = theirs.subject.clone();
    } else {
        merged.subject = yours.subject.clone();
    }

    // Merge points
    let mut all_themes: std::collections::HashSet<_> =
        yours_by_theme.keys().chain(theirs_by_theme.keys()).cloned().collect();

    for theme in all_themes {
        let base_point = base_by_theme.get(theme);
        let yours_point = yours_by_theme.get(theme);
        let theirs_point = theirs_by_theme.get(theme);

        match (base_point, yours_point, theirs_point) {
            // Both added/modified same point differently
            (_, Some(y), Some(t)) if y.stance != t.stance => {
                conflicts.push(MergeConflict::ConflictingStance {
                    theme: theme.clone(),
                    base: base_point.map(|p| p.stance.clone()).unwrap_or_default(),
                    yours: y.stance.clone(),
                    theirs: t.stance.clone(),
                });
                // Take yours for now
                merged.points.retain(|p| p.theme != theme);
                merged.points.push(y.clone());
            }
            // Only one side modified
            (_, Some(y), _) => {
                merged.points.retain(|p| p.theme != theme);
                merged.points.push(y.clone());
            }
            (_, _, Some(t)) => {
                merged.points.retain(|p| p.theme != theme);
                merged.points.push(t.clone());
            }
            // Both removed (no action needed)
            _ => {}
        }
    }

    Ok((merged, conflicts))
}
```

---

## Phase 5: Temporal Queries (Advanced)

### 5.1 Query as-of timestamp

```rust
pub fn get_worldview_at_time(
    slug: &str,
    at_time: chrono::DateTime<chrono::Utc>,
) -> Result<Worldview, Box<dyn std::error::Error>> {
    let conn = crate::storage::db::init_db()?;

    // Find latest version before or at time
    let data: String = conn.query_row(
        "SELECT data FROM worldview_versions
         WHERE slug = ? AND created_at <= ?
         ORDER BY version DESC
         LIMIT 1",
        params![slug, at_time.to_rfc3339()],
        |row| row.get(0),
    )?;

    Ok(serde_json::from_str(&data)?)
}

pub fn get_worldview_timeline(
    slug: &str,
    from: chrono::DateTime<chrono::Utc>,
    to: chrono::DateTime<chrono::Utc>,
) -> Result<Vec<(chrono::DateTime<chrono::Utc>, Worldview)>, Box<dyn std::error::Error>> {
    let conn = crate::storage::db::init_db()?;

    let mut stmt = conn.prepare(
        "SELECT created_at, data FROM worldview_versions
         WHERE slug = ? AND created_at BETWEEN ? AND ?
         ORDER BY version ASC",
    )?;

    let iter = stmt.query_map(
        params![slug, from.to_rfc3339(), to.to_rfc3339()],
        |row| {
            let timestamp_str: String = row.get(0)?;
            let data: String = row.get(1)?;
            Ok((
                timestamp_str.parse().unwrap_or_else(|_| chrono::Utc::now()),
                serde_json::from_str::<Worldview>(&data).unwrap(),
            ))
        },
    )?;

    let mut results = Vec::new();
    for item in iter {
        results.push(item?);
    }

    Ok(results)
}
```

---

## Integration Checklist

- [ ] Add `audit.rs` module with JSONL logging
- [ ] Update `json_store.rs::save_worldview()` to log audit entries
- [ ] Add `history` CLI command
- [ ] Add SQLite migration for `worldview_versions` table
- [ ] Add `versioning.rs` module for version queries
- [ ] Add `--from-version` / `--to-version` flags to `diff` command
- [ ] Add `json-patch` dependency and semantic diff functions
- [ ] Update CHANGELOG with versioning feature
- [ ] Test audit logging with manual edits
- [ ] Document version history workflow

---

## Data Format Examples

### Audit Entry
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-02-01T14:30:00Z",
  "operation": "update_points",
  "user": "alice",
  "wve_version": "0.8.0",
  "reason": "Increased AI confidence based on recent research",
  "before": {
    "slug": "ai-views",
    "subject": "Artificial Intelligence",
    "points": [
      {"theme": "AI", "stance": "cautious", "confidence": 0.7, ...}
    ]
  },
  "after": {
    "slug": "ai-views",
    "subject": "Artificial Intelligence",
    "points": [
      {"theme": "AI", "stance": "cautious", "confidence": 0.85, ...}
    ]
  },
  "changes": [
    {
      "path": "/points/0/confidence",
      "op": "replace",
      "old_value": 0.7,
      "new_value": 0.85
    }
  ]
}
```

### Version Info
```json
{
  "id": 1,
  "version": 1,
  "created_at": "2025-02-01T10:00:00Z",
  "created_by": "alice",
  "reason": "Initial worldview creation"
}
```

### JSON Patch (RFC 6902)
```json
[
  { "op": "replace", "path": "/points/0/stance", "value": "very_cautious" },
  { "op": "add", "path": "/points/1", "value": {...} },
  { "op": "remove", "path": "/points/2" }
]
```

---

## Testing Strategy

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audit_entry_serialization() {
        let entry = AuditEntry {
            id: "test".to_string(),
            timestamp: chrono::Utc::now(),
            operation: "update".to_string(),
            user: "test".to_string(),
            wve_version: "0.8.0".to_string(),
            reason: "Test".to_string(),
            before: None,
            after: serde_json::json!({}),
            changes: vec![],
            metadata: Default::default(),
        };

        let json = serde_json::to_string(&entry).unwrap();
        let parsed: AuditEntry = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.id, entry.id);
    }

    #[test]
    fn test_compute_changes() {
        // Test that changes are correctly identified
    }

    #[test]
    fn test_merge_worldviews_no_conflict() {
        // Test 3-way merge with non-overlapping changes
    }

    #[test]
    fn test_merge_worldviews_conflict() {
        // Test 3-way merge with overlapping changes
    }
}
```
