# Professional-Grade Versioned Storage for Rust Applications

A comprehensive guide to versioning strategies, storage backends, diffing, audit trails, and graph versioning for production Rust applications.

## 1. Versioning Strategies

### 1.1 Content-Addressable Storage (CAS)

**What it is**: Data is stored by its content's cryptographic hash rather than by filename or location. Like Git, the hash becomes the unique identifier.

**Advantages**:
- Perfect deduplication (identical content = identical hash)
- Cryptographic integrity verification
- Distributed-friendly (no central authority on naming)
- Immutable by design (changing content creates new hash)

**Rust Implementations**:
- **[Attaca](https://github.com/attaca/attaca)** - Distributed version control with upgradeable hashes and hashsplitting
- **[Vault](https://github.com/greglook/vault)** - Content-addressable, version-controlled hypermedia datastore
- **[CAS](https://github.com/dennwc/cas)** - Simple pragmatic implementation (influenced by Perkeep/Camlistore and Git)

**Typical Architecture**:
```rust
// Pseudocode pattern
use sha2::Sha256;

let content = serde_json::to_vec(&data)?;
let hash = Sha256::digest(&content);
let hash_str = format!("{:x}", hash);

// Store by hash
fs::write(format!(".store/{}", hash_str), content)?;

// Retrieve by hash
let retrieved = fs::read(format!(".store/{}", hash_str))?;
```

**When to use**:
- Need strong integrity guarantees
- Distributed or multi-client scenarios
- Long-term archival (content verified by hash)
- Deduplication is critical

**Trade-offs**:
- Requires mapping hashes back to human-readable names
- No direct filename browsing
- Storage layout is opaque

### 1.2 Structural Versioning vs Full Snapshots

**Full Snapshots**:
- Store complete copy on each version
- Pros: Simple, fast restore, no replay logic
- Cons: High storage, linear growth

**Structural Versioning**:
- Store only changed fields/properties
- Pros: Smaller storage, better for sparse changes
- Cons: Complex replay, must track all dependencies

**Hybrid Approach (Recommended)**:
- Full snapshots at major versions (e.g., every 100 commits)
- Delta storage between snapshots
- Balances simplicity with space efficiency

```rust
// Example: Snapshot + delta pattern
#[derive(Serialize, Deserialize)]
pub struct Worldview {
    pub version: u64,
    pub snapshot_hash: Option<String>, // Points to last full snapshot
    pub deltas: Vec<Delta>,            // Changes since snapshot
}

#[derive(Serialize, Deserialize)]
pub struct Delta {
    pub timestamp: DateTime<Utc>,
    pub changes: Vec<Change>,
}

// Reconstruct by loading snapshot + replaying deltas
fn reconstruct(version: u64) -> Result<Worldview> {
    let snapshot = load_snapshot(version)?;
    let deltas = load_deltas_since(&snapshot.hash, version)?;
    Ok(apply_deltas(snapshot, deltas))
}
```

### 1.3 Delta Storage

**Approach**: Store only differences between versions, rebuild by replaying.

**Libraries**:
- **[serde-diff](https://crates.io/crates/serde-diff)** - Serialize diff of two structs
- **[json-patch](https://github.com/scrtlabs/json-patch)** - RFC 6902 (JSON Patch) & RFC 7396 (JSON Merge Patch)

**Pros**:
- Minimal storage per version
- Natural for incremental changes
- Works with standard patch formats

**Cons**:
- Slow access to old versions (must replay)
- Sensitive to early delta corruption
- Complex conflict resolution

**Example with json-patch**:
```rust
use json_patch::{json_patch, diff};

let old: serde_json::Value = serde_json::json!({
    "points": [
        {"theme": "AI", "stance": "cautious"}
    ]
});

let new: serde_json::Value = serde_json::json!({
    "points": [
        {"theme": "AI", "stance": "cautious"},
        {"theme": "Climate", "stance": "urgent"}
    ]
});

// Generate RFC 6902 patch
let patch = diff(&old, &new);
// Can be stored, transmitted, replayed
let result = json_patch(&mut old.clone(), &patch)?;
assert_eq!(result, new);
```

### 1.4 Time-Travel/Temporal Queries

**Concept**: Ability to query the system as it existed at any point in time.

**RDF/Triple Store Approach**:
- Attach timestamps to each triple
- Use SPARQL with temporal filters
- Example: `SELECT * WHERE { ?s ?p ?o . FILTER(?timestamp <= 2024-01-15) }`

**Event Sourcing Approach**:
- Store immutable event log
- Replay events up to timestamp to reconstruct state
- Allows "what if" scenarios

**Implementation Pattern**:
```rust
pub struct Event {
    pub timestamp: DateTime<Utc>,
    pub entity_id: String,
    pub change: ChangeType,
    pub snapshot_at: Option<DateTime<Utc>>, // For efficient binary search
}

pub fn query_at_time(entity_id: &str, at_time: DateTime<Utc>) -> Result<Worldview> {
    // Find nearest snapshot before or at time
    let snapshot = find_snapshot(entity_id, at_time)?;

    // Replay events between snapshot and target time
    let events = get_events_in_range(entity_id, snapshot.at, at_time)?;

    let mut state = snapshot.state;
    for event in events {
        state = apply_event(&state, &event)?;
    }
    Ok(state)
}
```

---

## 2. Storage Backends

### 2.1 SQLite + Schema Versioning

**Best For**: Structured data, relational queries, single-file deployability

**Crates**:
- **[rusqlite](https://crates.io/crates/rusqlite)** - Direct bindings (synchronous, embedded)
- **[sqlx](https://github.com/launchbadly/sqlx)** - Async, compile-time checked queries
- **[rusqlite_migration](https://crates.io/crates/rusqlite_migration)** - Lightweight migration using `user_version`
- **[refinery](https://github.com/rust-db/refinery)** - Powerful migration toolkit (supports Postgres, MySQL, SQLite)
- **[turbosql](https://github.com/trevyn/turbosql)** - Derive macro that generates migrations from Rust structs

**Schema Versioning Strategy**:

1. **Using `user_version` pragma** (simplest):
   ```rust
   use rusqlite::Connection;

   let conn = Connection::open("app.db")?;

   // Get current schema version
   let version: i32 = conn.query_row("PRAGMA user_version", [], |row| row.get(0))?;

   // Apply migrations if needed
   if version < 1 {
       conn.execute("CREATE TABLE worldviews (...)", [])?;
       conn.execute("PRAGMA user_version = 1", [])?;
   }
   if version < 2 {
       conn.execute("ALTER TABLE worldviews ADD COLUMN new_column TEXT", [])?;
       conn.execute("PRAGMA user_version = 2", [])?;
   }
   ```

2. **Using migrations table** (more flexible):
   ```rust
   // With refinery or rusqlite_migration
   // Tracks applied migrations, supports rollback semantics
   ```

3. **TurboSQL approach** (compile-time):
   ```rust
   use turbosql::{Turbosql, select};

   #[derive(Turbosql, Default)]
   pub struct Worldview {
       rowid: Option<i64>,
       pub slug: String,
       pub subject: String,
       pub created_at: String,
       // Migrations generated automatically from struct changes
   }
   ```

**Versioning Worldview Data**:
```rust
#[derive(Serialize, Deserialize)]
pub struct WorldviewVersion {
    pub version: i64,
    pub worldview_id: i64,
    pub data: String, // JSON blob of full snapshot
    pub created_at: DateTime<Utc>,
    pub created_by: String,
    pub reason: String, // Commit message
}

// Schema
/*
CREATE TABLE worldview_versions (
    id INTEGER PRIMARY KEY,
    worldview_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    data TEXT NOT NULL,           -- Full JSON snapshot
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    UNIQUE(worldview_id, version)
);
CREATE INDEX idx_worldview_version ON worldview_versions(worldview_id, version DESC);
*/
```

**Advantages**:
- Single file deployment
- ACID transactions
- Strong consistency
- JSON1 extension for document-like storage
- Full-text search (FTS5)
- Common (most developers know SQL)

**Disadvantages**:
- Single-writer at a time (locking)
- Schema evolution requires careful migration
- Not ideal for highly concurrent writes

### 2.2 RocksDB

**Best For**: Write-heavy workloads, time-series, high-throughput scenarios

**Characteristics**:
- Key-value store optimized for SSDs
- LSM tree structure (writes fast, reads require traversal)
- Compression, WAL, background compaction
- Not relational (no joins, aggregations)

**Rust Bindings**:
- **[rocksdb](https://crates.io/crates/rocksdb)** - Official C++ bindings
- **[fjall](https://github.com/fjall-rs/fjall)** - Pure Rust LSM tree (RocksDB-like)

**For Versioning**:
```rust
use rocksdb::DB;

let db = DB::open_default("worldviews.db")?;

// Store with version in key
let key = format!("worldview:{}:v{}", slug, version);
db.put(key.as_bytes(), &serialized_data)?;

// Retrieve specific version
let value = db.get(key.as_bytes())?;

// List all versions (must enumerate keys with prefix)
for (key, _) in db.iterator(rocksdb::IteratorMode::From(b"worldview:myslug", rocksdb::Direction::Forward)) {
    if key.starts_with(b"worldview:myslug:") {
        println!("{:?}", key);
    }
}
```

**Advantages**:
- Exceptional write performance
- Efficient range queries (by key prefix)
- Compression built-in
- Good for version chains (key = slug:version)

**Disadvantages**:
- No query language (pure K-V)
- Complex configuration tuning
- Not transactional across keys
- Heavier operational overhead

### 2.3 Embedding Git with git2-rs

**Best For**: Deep version control semantics, branching, merging, distributed workflows

**Crate**: **[git2-rs](https://github.com/rust-lang/git2-rs)** - Safe Rust bindings to libgit2

**Usage**:
```rust
use git2::{Repository, Signature};
use std::path::Path;

// Initialize or open repo
let repo = Repository::init(Path::new(".wve-store"))?;

// Store worldview data
let path = format!("worldviews/{}.json", slug);
fs::write(&path, serde_json::to_string_pretty(&worldview)?)?;

// Commit (version)
let mut index = repo.index()?;
index.add_path(Path::new(&path))?;
index.write()?;

let tree_id = index.write_tree()?;
let tree = repo.find_tree(tree_id)?;
let parent = repo.head().ok().and_then(|r| r.peel_to_commit().ok());
let parents = parent.as_ref().map(|p| vec![p]).unwrap_or_default();

let sig = Signature::now("wve", "wve@local")?;
repo.commit(
    Some("HEAD"),
    &sig,
    &sig,
    &format!("Add/update worldview: {}", slug),
    &tree,
    parents.iter().collect::<Vec<_>>().as_slice(),
)?;
```

**When to use**:
- Need full Git semantics (branches, tags, merges)
- Multi-user collaborative editing
- Want standard Git tools (diff, log, blame)
- Need distributed/offline capability

**Limitations**:
- Large repo can be slow (Git was designed for source code)
- Schema changes require careful migration
- Not ideal for frequent small updates

### 2.4 Custom JSONL-Based Versioning

**Best For**: Audit trails, append-only logs, event sourcing

**Pattern**:
```rust
use std::fs::OpenOptions;
use std::io::{BufWriter, Write};

// Store as JSONL (one JSON per line, no modification)
let mut file = OpenOptions::new()
    .create(true)
    .append(true)
    .open(format!(".wve/store/{}/history.jsonl", slug))?;

let mut writer = BufWriter::new(file);

#[derive(Serialize)]
struct LogEntry {
    timestamp: DateTime<Utc>,
    version: u64,
    operation: String,
    data: serde_json::Value,
    metadata: HashMap<String, String>,
}

let entry = LogEntry {
    timestamp: Utc::now(),
    version: current_version,
    operation: "update_points".to_string(),
    data: serde_json::to_value(&worldview)?,
    metadata: {
        let mut m = HashMap::new();
        m.insert("user".to_string(), "cli".to_string());
        m.insert("reason".to_string(), "Manual edit".to_string());
        m
    }
};

writeln!(writer, "{}", serde_json::to_string(&entry)?)?;
```

**Advantages**:
- Immutable by design (never modify, only append)
- Simple tooling (grep, jq work natively)
- Git-friendly (text format, diffs work)
- Excellent audit trail
- Survives schema migrations (data is self-describing)

**Disadvantages**:
- Slow random access (must scan file)
- Large files over time
- No transactions across entries
- Requires external indexing for performance

**Recommended**: Hybrid approach:
- JSONL for audit log (immutable, always appended)
- SQLite index for fast lookups
- Periodic snapshots to JSONL for archival

---

## 3. Diffing Strategies

### 3.1 JSON Diff Libraries

**For Worldviews** (which are JSON), the best options:

#### json-patch (RFC 6902 / RFC 7396)

**Crate**: [json-patch](https://crates.io/crates/json-patch)

**RFC 6902 (JSON Patch)**:
```rust
use json_patch::{json_patch, diff, Patch};
use serde_json::json;

let old = json!({
    "points": [
        {"theme": "AI", "stance": "cautious"}
    ]
});

let new = json!({
    "points": [
        {"theme": "AI", "stance": "very_cautious"},
        {"theme": "Climate", "stance": "urgent"}
    ]
});

// Generate patch
let patch = diff(&old, &new);
println!("{}", serde_json::to_string_pretty(&patch)?);
// Output:
// [
//   { "op": "replace", "path": "/points/0/stance", "value": "very_cautious" },
//   { "op": "add", "path": "/points/1", "value": {...} }
// ]

// Apply patch
let mut patched = old.clone();
json_patch(&mut patched, &patch)?;
assert_eq!(patched, new);
```

**RFC 7396 (JSON Merge Patch)**:
```rust
use json_patch::merge;

let base = json!({"a": 1, "b": 2});
let patch = json!({"b": 3, "c": 4});

let result = merge(&base, &patch)?;
// Result: {"a": 1, "b": 3, "c": 4}
```

#### jsondiffpatch

**Crate**: [jsondiffpatch](https://crates.io/crates/jsondiffpatch)

Advanced diff/patch with:
- Array/object diff
- Text diff (via `similar` crate)
- Multiple output formats
- Human-readable deltas

```rust
use jsondiffpatch::{Differ, Patcher};

let differ = Differ::new();
let patcher = Patcher::new();

let old = json!({"points": [...]});
let new = json!({"points": [...]});

let delta = differ.diff(&old, &new);
let patched = patcher.patch(&old, &delta)?;
```

### 3.2 Structural Diffing for Worldviews

**The Challenge**: What makes a good diff for worldviews (beliefs)?

**Semantic vs Syntactic Diff**:
- **Syntactic**: "Added a point, removed stance field" (what changed)
- **Semantic**: "Shifted stance on AI from cautious to very_cautious" (why it matters)

**Recommendation**: Hybrid approach

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WorldviewChange {
    PointAdded {
        theme: String,
        stance: String,
    },
    PointRemoved {
        theme: String,
    },
    StanceChanged {
        theme: String,
        old_stance: String,
        new_stance: String,
    },
    ConfidenceAdjusted {
        theme: String,
        old_confidence: f64,
        new_confidence: f64,
    },
    EvidenceAdded {
        theme: String,
        evidence: String,
    },
}

pub fn diff_worldviews(old: &Worldview, new: &Worldview) -> Vec<WorldviewChange> {
    let mut changes = Vec::new();

    let old_by_theme: HashMap<_, _> = old.points.iter().map(|p| (&p.theme, p)).collect();
    let new_by_theme: HashMap<_, _> = new.points.iter().map(|p| (&p.theme, p)).collect();

    // Detect point removals and stance changes
    for (theme, old_point) in &old_by_theme {
        if let Some(new_point) = new_by_theme.get(theme) {
            if old_point.stance != new_point.stance {
                changes.push(WorldviewChange::StanceChanged {
                    theme: theme.to_string(),
                    old_stance: old_point.stance.clone(),
                    new_stance: new_point.stance.clone(),
                });
            }
            if (old_point.confidence - new_point.confidence).abs() > 0.01 {
                changes.push(WorldviewChange::ConfidenceAdjusted {
                    theme: theme.to_string(),
                    old_confidence: old_point.confidence,
                    new_confidence: new_point.confidence,
                });
            }
        } else {
            changes.push(WorldviewChange::PointRemoved { theme: theme.to_string() });
        }
    }

    // Detect point additions
    for (theme, new_point) in &new_by_theme {
        if !old_by_theme.contains_key(theme) {
            changes.push(WorldviewChange::PointAdded {
                theme: theme.to_string(),
                stance: new_point.stance.clone(),
            });
        }
    }

    changes
}
```

### 3.3 Three-Way Merge for Collaborative Editing

**Use Case**: Two users edit a worldview independently; merge their changes.

**Crates**:
- **[threeway_merge](https://crates.io/crates/threeway_merge)** - Git-style 3-way string merging
- **[diffy](https://docs.rs/diffy)** - Myers' diff algorithm (good for text)
- **[similar](https://github.com/mitsuhiko/similar)** - High-level diffing library
- **[heckdiff](https://github.com/phynalle/heckdiff)** - Dedicated 3-way merge tool in Rust

**Algorithm**:
1. Take three inputs: `base`, `yours` (local), `theirs` (remote)
2. Find changes from base→yours and base→theirs
3. If changes don't overlap, auto-merge
4. If they overlap, mark as conflict

```rust
use threeway_merge::merge;

let base = r#"points:
  - theme: AI
    stance: cautious
"#;

let yours = r#"points:
  - theme: AI
    stance: very_cautious
  - theme: Privacy
    stance: essential
"#;

let theirs = r#"points:
  - theme: AI
    stance: cautious
  - theme: Climate
    stance: urgent
"#;

let result = merge(base, yours, theirs)?;
// Auto-merged (both added different points)
```

### 3.4 Conflict Resolution Strategies

**For Complex Data (Worldviews)**: No one-size-fits-all approach.

**Strategy 1: Manual Resolution**
```rust
#[derive(Debug)]
pub enum MergeConflict {
    ConflictingStance {
        theme: String,
        base: String,
        yours: String,
        theirs: String,
    },
}

pub fn merge_worldviews(base: &Worldview, yours: &Worldview, theirs: &Worldview)
    -> Result<(Worldview, Vec<MergeConflict>)>
{
    let mut conflicts = Vec::new();
    let mut merged = base.clone();

    for your_point in &yours.points {
        let their_point = theirs.points.iter().find(|p| p.theme == your_point.theme);

        if let Some(their_point) = their_point {
            if your_point.stance != their_point.stance {
                // Conflict: both changed the same point differently
                conflicts.push(MergeConflict::ConflictingStance {
                    theme: your_point.theme.clone(),
                    base: base.points.iter()
                        .find(|p| p.theme == your_point.theme)
                        .map(|p| p.stance.clone())
                        .unwrap_or_default(),
                    yours: your_point.stance.clone(),
                    theirs: their_point.stance.clone(),
                });
            }
        } else {
            // No conflict, add your point
            merged.points.push(your_point.clone());
        }
    }

    Ok((merged, conflicts))
}
```

**Strategy 2: CRDTs (Automatic Conflict Resolution)**

**Concept**: Data structure designed so that any two versions can be merged without manual intervention.

**Crates**:
- **[automerge](https://crates.io/crates/automerge)** - JSON CRDT (Rust rewrite)
- **[deepmerge](https://crates.io/crates/deepmerge)** - Policy-driven deep merge

**CRDT Approach**:
```rust
use automerge::{AutoCommit, Value, ObjType};

let mut doc = AutoCommit::new();

// User A's changes
let mut a_doc = doc.clone();
a_doc.put_object(automerge::ROOT, "ai_stance", ObjType::Map)?;
a_doc.put(automerge::ROOT, "ai_stance", "very_cautious")?;

// User B's changes
let mut b_doc = doc.clone();
b_doc.put_object(automerge::ROOT, "climate_stance", ObjType::Map)?;
b_doc.put(automerge::ROOT, "climate_stance", "urgent")?;

// Merge automatically (no conflicts, different fields)
a_doc.merge(b_doc)?;
// Result: both stances present, no manual conflict resolution needed
```

**Trade-offs**:
- CRDTs add storage overhead (track enough history for merge)
- Better for collaborative, distributed scenarios
- Complex semantics (last-write-wins on conflicts, not semantic)

---

## 4. Audit Trails

### 4.1 Immutable Audit Logs

**Pattern: Event Sourcing**

```rust
#[derive(Serialize, Deserialize, Clone)]
pub struct AuditEntry {
    pub id: String,                      // Unique identifier (UUID)
    pub timestamp: DateTime<Utc>,        // When
    pub entity_type: String,             // "worldview"
    pub entity_id: String,               // Which worldview (slug)
    pub operation: String,               // "create", "update_stance", etc.
    pub user: String,                    // Who (email, CLI, etc.)
    pub tool_version: String,            // Which version of wve
    pub reason: String,                  // Why (commit message)
    pub before: Option<serde_json::Value>,
    pub after: serde_json::Value,
    pub changes: Vec<Change>,            // Structural changes
    pub metadata: HashMap<String, String>,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct Change {
    pub path: String,                    // JSON path: /points/0/stance
    pub op: String,                      // "add", "remove", "replace"
    pub old_value: Option<serde_json::Value>,
    pub new_value: Option<serde_json::Value>,
}

// Storage: JSONL file (immutable append-only)
// ~/.wve/store/my-worldview/audit.jsonl
```

**Schema for Audit Table (SQLite)**:
```sql
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,          -- ISO 8601
    entity_type TEXT NOT NULL,        -- "worldview"
    entity_id TEXT NOT NULL,          -- slug
    operation TEXT NOT NULL,          -- "update_stance"
    "user" TEXT NOT NULL,             -- who made change
    tool_version TEXT NOT NULL,       -- "0.7.0"
    reason TEXT NOT NULL,             -- commit message
    before_snapshot TEXT,             -- Full JSON snapshot (nullable)
    after_snapshot TEXT NOT NULL,     -- Full JSON snapshot
    changes_json TEXT NOT NULL,       -- JSON array of changes
    metadata_json TEXT,               -- Extra key-value pairs

    UNIQUE(id),
    INDEX idx_entity_time ON (entity_id, timestamp DESC),
    INDEX idx_user_time ON ("user", timestamp DESC)
);
```

### 4.2 User Tracking

```rust
pub struct UserContext {
    pub user: String,                      // "user@example.com" or "cli"
    pub tool_version: String,              // Cargo.toml version
    pub session_id: String,                // Session UUID
    pub reason: String,                    // --reason flag
}

// In CLI:
let context = UserContext {
    user: std::env::var("USER").unwrap_or_else(|_| "unknown".to_string()),
    tool_version: env!("CARGO_PKG_VERSION").to_string(),
    session_id: uuid::Uuid::new_v4().to_string(),
    reason: args.reason,
};
```

### 4.3 Rollback Capabilities

```rust
pub fn rollback_to_version(entity_id: &str, target_version: u64) -> Result<Worldview> {
    // Find the version entry
    let version_entry = db.query_row(
        "SELECT data FROM worldview_versions WHERE entity_id = ? AND version = ?",
        params![entity_id, target_version],
        |row| row.get::<_, String>(0)
    )?;

    let worldview: Worldview = serde_json::from_str(&version_entry)?;

    // Record the rollback in audit log
    let audit = AuditEntry {
        id: uuid::Uuid::new_v4().to_string(),
        timestamp: Utc::now(),
        operation: "rollback".to_string(),
        user: context.user.clone(),
        reason: format!("Rolled back to version {}", target_version),
        before: Some(serde_json::to_value(&current)?),
        after: serde_json::to_value(&worldview)?,
        ..
    };
    log_audit_entry(&audit)?;

    // Save as new version
    save_worldview_version(entity_id, &worldview, &audit)?;

    Ok(worldview)
}
```

---

## 5. Migration & Compatibility

### 5.1 Schema Migrations Without Data Loss

**Using rusqlite_migration**:
```rust
use rusqlite_migration::{Migrations, M};

let migrations = Migrations::new(vec![
    M::up("CREATE TABLE worldviews (id INTEGER PRIMARY KEY, slug TEXT UNIQUE)"),
    M::up("CREATE TABLE worldview_versions (id INTEGER PRIMARY KEY, worldview_id INTEGER)"),
    M::up("ALTER TABLE worldviews ADD COLUMN subject TEXT DEFAULT ''"),
    // Reversible migration
    M::up_down(
        "ALTER TABLE worldviews ADD COLUMN archived INTEGER DEFAULT 0",
        "ALTER TABLE worldviews DROP COLUMN archived"
    ),
]);

let conn = Connection::open("app.db")?;
migrations.to_latest(&conn)?;
```

### 5.2 Backward Compatibility Layers

```rust
#[derive(Serialize, Deserialize)]
pub struct WorldviewV1 {
    pub slug: String,
    pub subject: String,
    pub points: Vec<WorldviewPointV1>,
}

#[derive(Serialize, Deserialize)]
pub struct WorldviewPointV1 {
    pub theme: String,
    pub stance: String,
}

// Newer version adds confidence and evidence
#[derive(Serialize, Deserialize)]
pub struct WorldviewV2 {
    pub slug: String,
    pub subject: String,
    pub points: Vec<WorldviewPointV2>,
}

#[derive(Serialize, Deserialize)]
pub struct WorldviewPointV2 {
    pub theme: String,
    pub stance: String,
    #[serde(default)]
    pub confidence: f64,
    #[serde(default)]
    pub evidence: Vec<String>,
}

// Upgrade function
pub fn upgrade_v1_to_v2(v1: WorldviewV1) -> WorldviewV2 {
    WorldviewV2 {
        slug: v1.slug,
        subject: v1.subject,
        points: v1.points.into_iter().map(|p| WorldviewPointV2 {
            theme: p.theme,
            stance: p.stance,
            confidence: 0.5,  // Default for migrated data
            evidence: vec![],
        }).collect(),
    }
}

// Load with version detection
pub fn load_worldview(slug: &str) -> Result<WorldviewV2> {
    let json = fs::read_to_string(format!(".wve/store/{}/worldview.json", slug))?;
    let value: serde_json::Value = serde_json::from_str(&json)?;

    // Detect version based on schema
    if value.get("points").and_then(|p| p[0].get("confidence")).is_none() {
        // V1 format
        let v1: WorldviewV1 = serde_json::from_value(value)?;
        Ok(upgrade_v1_to_v2(v1))
    } else {
        // V2+ format
        serde_json::from_value(value).map_err(|e| e.into())
    }
}
```

### 5.3 Data Export for Long-Term Archival

```rust
pub fn export_worldview_complete(slug: &str) -> Result<Export> {
    let worldview = load_worldview(slug)?;

    let versions = get_all_versions(slug)?;
    let audit_log = get_audit_log(slug)?;

    let export = Export {
        export_timestamp: Utc::now(),
        export_format_version: "1.0.0".to_string(),
        wve_version: env!("CARGO_PKG_VERSION").to_string(),
        worldview: worldview,
        all_versions: versions,
        audit_log: audit_log,
        // Add schema documentation
        schema: r#"
        Worldview {
            slug: String,
            subject: String,
            points: Vec<{
                theme: String,
                stance: String,
                confidence: f64,
                evidence: Vec<String>,
                sources: Vec<String>
            }>
        }
        "#.to_string(),
    };

    // Export as standalone JSON or tar.gz
    let json = serde_json::to_string_pretty(&export)?;
    fs::write(format!("{}-export.json", slug), json)?;

    Ok(export)
}
```

---

## 6. Graph/Relationship Versioning

### 6.1 Versioning Interconnected Data (People → Beliefs → Concepts)

**The Challenge**: Worldviews aren't isolated; they relate to:
- Other people (disagreements, influences)
- Concepts (AI, Climate, Privacy)
- Sources (papers, articles)

**Approach 1: Temporal Graphs with Snapshots**

```rust
#[derive(Serialize, Deserialize)]
pub struct TemporalGraph {
    pub timestamp: DateTime<Utc>,
    pub entities: HashMap<String, Entity>,
    pub edges: Vec<Edge>,
}

#[derive(Serialize, Deserialize)]
pub struct Entity {
    pub id: String,
    pub entity_type: String, // "person", "worldview", "concept", "source"
    pub data: serde_json::Value,
}

#[derive(Serialize, Deserialize)]
pub struct Edge {
    pub from: String,
    pub to: String,
    pub relation_type: String, // "authored", "references", "disagrees_with"
    pub properties: HashMap<String, String>,
}

// Storage: Snapshot every major version
pub fn snapshot_graph(timestamp: DateTime<Utc>, entities: &HashMap<String, Entity>,
                      edges: &[Edge]) -> Result<String> {
    let graph = TemporalGraph {
        timestamp,
        entities: entities.clone(),
        edges: edges.to_vec(),
    };

    let path = format!(".wve/graph/{}.json", timestamp.timestamp());
    fs::write(&path, serde_json::to_string_pretty(&graph)?)?;
    Ok(path)
}
```

**Approach 2: RDF/Triple Store with Temporal Metadata**

Using SPARQL-queryable format:

```turtle
# RDF with temporal annotations
@prefix wv: <http://wve.local/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix prov: <http://www.w3.org/ns/prov#> .

# Entity
wv:alice_worldview a wv:Worldview ;
    dcterms:subject "AI Safety" ;
    dcterms:created "2025-01-01"^^xsd:dateTime ;
    dcterms:modified "2025-02-01"^^xsd:dateTime .

# Belief (RDF statement with metadata)
wv:alice_ai_belief rdf:subject wv:alice_worldview ;
    rdf:predicate wv:hasStance ;
    rdf:object wv:very_cautious ;
    dcterms:issued "2025-01-15"^^xsd:dateTime ;
    wv:confidence 0.85 ;
    prov:wasAttributedTo wv:alice .

# Relationship between worldviews
wv:alice_worldview wv:disagreesWithOn wv:bob_worldview ;
    wv:topic "AI_Safety" ;
    dcterms:issued "2025-01-20"^^xsd:dateTime .
```

**Rust Implementation with OxRDF/Oxigraph**:
```rust
use oxigraph::{MemoryStore, model::*};

let store = MemoryStore::new();

// Add RDF triple
let subject = NamedNode::new("http://wve.local/alice_worldview")?;
let predicate = NamedNode::new("http://wve.local/hasStance")?;
let object = Literal::new_simple_literal("very_cautious");

store.insert(Triple::new(subject, predicate, object));

// Query with timestamp constraint
let query = r#"
SELECT ?person ?stance ?date WHERE {
    ?person wv:hasStance ?stance ;
            dcterms:issued ?date .
    FILTER (?date < "2025-02-01"^^xsd:dateTime)
}
"#;
```

### 6.2 Temporal Graph Queries

```rust
// Time-travel query: "What did Alice believe on 2025-01-15?"
pub fn query_at_time(entity_id: &str, timestamp: DateTime<Utc>) -> Result<TemporalGraph> {
    // Load all snapshots before timestamp
    let snapshots = find_snapshots_before(timestamp)?;

    // Get most recent snapshot
    let most_recent = snapshots.last().ok_or("No snapshots")?;
    let mut graph: TemporalGraph = serde_json::from_str(&most_recent)?;

    // Replay diffs from snapshot to target time
    let diffs = get_diffs_in_range(&most_recent.timestamp, timestamp)?;
    for diff in diffs {
        apply_diff_to_graph(&mut graph, &diff)?;
    }

    Ok(graph)
}

// Range query: "Show evolution of Alice's stance from Jan-Feb 2025"
pub fn timeline(entity_id: &str, from: DateTime<Utc>, to: DateTime<Utc>)
    -> Result<Vec<(DateTime<Utc>, serde_json::Value)>>
{
    let audit_log = get_audit_log_range(entity_id, from, to)?;

    let timeline = audit_log.into_iter().map(|entry| {
        (entry.timestamp, entry.after)
    }).collect();

    Ok(timeline)
}
```

### 6.3 Property Graphs vs RDF Triple Stores

**Property Graphs** (e.g., Neo4j):
- Nodes have properties (key-value)
- Edges have types and properties
- Efficient storage and querying
- Not standardized (proprietary)

**RDF Triple Stores** (e.g., Oxigraph):
- Standardized (RDF, SPARQL)
- Subject-Predicate-Object statements
- Better for inference and knowledge graphs
- Verbose, larger storage

**For Worldviews**: Property graph is simpler

```rust
// Property graph model
#[derive(Serialize, Deserialize)]
pub struct PropertyGraph {
    pub nodes: Vec<Node>,
    pub edges: Vec<PropertyEdge>,
}

#[derive(Serialize, Deserialize)]
pub struct Node {
    pub id: String,
    pub labels: Vec<String>, // ["Worldview", "Alice"]
    pub properties: HashMap<String, Value>,
}

#[derive(Serialize, Deserialize)]
pub struct PropertyEdge {
    pub id: String,
    pub from: String,
    pub to: String,
    pub relation: String,
    pub properties: HashMap<String, Value>,
}
```

---

## 7. Recommended Architecture for Weave

### 7.1 Short-Term (Current State)

Current structure (JSON files + SQLite index) is **good for MVP**:
- Simple, works offline
- Audit trail with JSONL
- Schema migrations straightforward

**Enhancements**:
1. Add versioning table to SQLite
2. Use json-patch for compact diffs
3. Implement AuditEntry logging (JSONL)
4. Add three-way merge for collaboration

### 7.2 Medium-Term (v1.0)

Recommended stack:
- **Storage**: SQLite (structured data) + JSONL (audit log)
- **Diffing**: json-patch (RFC 6902) + semantic diffs
- **Versioning**: Snapshot + delta with periodic full snapshots
- **Migration**: rusqlite_migration with backward compatibility layer
- **Graphs**: Temporal snapshots with timestamps

**Add**:
- Graph relationships (SQLite with junction tables)
- Temporal queries
- Merge conflict detection

### 7.3 Long-Term (Enterprise)

If scaling beyond single user:
- Consider **RocksDB** for write-heavy scenarios
- Embed **git2-rs** for full version control semantics
- Use **CRDTs** (Automerge) for collaborative editing
- Event sourcing with CQRS pattern
- RDF triple store for complex knowledge graphs

---

## Crate Recommendations Summary

| Task | Crate(s) | Pros | Cons |
|------|---------|------|------|
| **Storage (Relational)** | rusqlite, sqlx | Simple, ACID, portable | Single writer |
| **Storage (KV)** | rocksdb, fjall | Fast writes, range queries | No relations |
| **Schema Migrations** | rusqlite_migration, refinery | Lightweight, Git-friendly | Manual SQL |
| **Version Control** | git2-rs | Full semantics, tools | Slow for large repos |
| **JSON Diffing** | json-patch | RFC standard, compact | Basic semantics |
| **Advanced Diffing** | jsondiffpatch, similar | Multiple formats, text diff | Heavier |
| **Three-Way Merge** | threeway_merge, diffy | Proven algorithms | String-based |
| **Event Sourcing** | EventLog patterns (JSONL) | Immutable, audit-friendly | Must replay for queries |
| **Temporal Graphs** | Custom + RDF (Oxigraph) | Powerful queries | Complexity, standards learning |
| **Conflict Resolution** | automerge (CRDTs) | Automatic merge | Storage overhead |
| **Deep Merge** | deepmerge | Policy-driven, flexible | Less for semantic diffs |

---

## References

**Content-Addressable Storage & Versioning**:
- [Attaca - Distributed VCS](https://github.com/attaca/attaca)
- [Vault - Content-addressable datastore](https://github.com/greglook/vault)
- [Git internals - Content-addressable storage](https://medium.com/the-software-journal/why-git-is-fast-a-practical-look-at-content-addressable-storage-85903734429f)

**JSON Diffing & Patching**:
- [json-patch crate (RFC 6902/7396)](https://crates.io/crates/json-patch)
- [jsondiffpatch](https://crates.io/crates/jsondiffpatch)
- [serde-diff](https://crates.io/crates/serde-diff)

**Three-Way Merge**:
- [threeway_merge crate](https://crates.io/crates/threeway_merge)
- [diffy crate](https://docs.rs/diffy)
- [heckdiff (GitHub)](https://github.com/phynalle/heckdiff)

**SQL Migrations**:
- [rusqlite_migration](https://crates.io/crates/rusqlite_migration)
- [refinery](https://github.com/rust-db/refinery)
- [turbosql](https://github.com/trevyn/turbosql)

**Embedded Databases**:
- [rocksdb comparison (W3Resource)](https://www.w3resource.com/sqlite/snippets/rocksdb-vs-sqlite.php)
- [Fjall (Pure Rust LSM)](https://github.com/fjall-rs/fjall)
- [HackerNoon - Embedded DB comparison](https://hackernoon.com/a-closer-look-at-the-top-3-embedded-databases-sqlite-rocksdb-and-duckdb)

**Version Control Integration**:
- [git2-rs (Rust Git bindings)](https://crates.io/crates/git2)
- [git2-rs documentation](https://docs.rs/git2)

**Event Sourcing & CQRS**:
- [CQRS and Event Sourcing using Rust (Official docs)](https://doc.rust-cqrs.org/)
- [Event Sourcing in Rust (Medium)](https://ariseyhun.medium.com/event-sourcing-in-rust-f9aa0f79d6c5)

**Graphs & Knowledge Representation**:
- [RDF vs Property Graphs (Neo4j)](https://neo4j.com/blog/knowledge-graph/rdf-vs-property-graphs-knowledge-graphs/)
- [RDF Triple Stores (Ontotext)](https://www.ontotext.com/knowledgehub/fundamentals/what-is-rdf-triplestore/)
- [IndraDB (Rust graph database)](https://github.com/indradb/indradb)
- [Oxigraph/OxRDF (SPARQL in Rust)](https://crates.io/crates/oxigraph)

**Conflict Resolution**:
- [CRDT Dictionary](https://www.iankduncan.com/engineering/2025-11-27-crdt-dictionary/)
- [deepmerge crate](https://crates.io/crates/deepmerge)
- [Automerge (JSON CRDT)](https://crates.io/crates/automerge)
