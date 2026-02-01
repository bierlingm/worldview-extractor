# Storage Decision Matrix for Weave

Quick reference for choosing versioning patterns based on requirements.

## Quick Decision Tree

```
START: What's your primary constraint?

├─ "Single user, simple offline use"
│  └─ Use: SQLite + JSONL audit log (Phase 1-2)
│     Files: ~/.wve/store/{slug}/worldview.json + audit.jsonl
│     Complexity: ⭐ Low
│     Effort: ⭐ Low
│
├─ "Need to see who changed what and when"
│  └─ Use: SQLite versioning table + audit trail (Phase 2)
│     Add: worldview_versions table
│     Complexity: ⭐⭐ Medium
│     Effort: ⭐⭐ Medium
│
├─ "Want to compare any two versions easily"
│  └─ Use: json-patch for compact diffs (Phase 3)
│     Crate: json-patch
│     Complexity: ⭐⭐⭐ Medium
│     Effort: ⭐⭐ Medium
│
├─ "Multiple users collaborating"
│  └─ Use: Three-way merge + conflict detection (Phase 4)
│     Crate: threeway_merge
│     Complexity: ⭐⭐⭐ Medium
│     Effort: ⭐⭐⭐ Medium
│
├─ "Query 'what did Alice believe on Jan 15?'"
│  └─ Use: Temporal queries on version history (Phase 5)
│     Requires: Phase 2 completed
│     Complexity: ⭐⭐ Medium
│     Effort: ⭐⭐ Low (given Phase 2)
│
├─ "Need full Git semantics (branches, tags, diffs)"
│  └─ Use: git2-rs embedding (Phase 6, Long-term)
│     Crate: git2
│     Complexity: ⭐⭐⭐⭐ High
│     Effort: ⭐⭐⭐⭐ High
│
├─ "Massive write load, temporal graphs"
│  └─ Use: RocksDB + temporal snapshots (Enterprise)
│     Crate: rocksdb
│     Complexity: ⭐⭐⭐⭐ Very High
│     Effort: ⭐⭐⭐⭐ Very High
│
└─ "Complex knowledge graphs, reasoning"
   └─ Use: RDF triple store (Enterprise)
      Crate: oxigraph (SPARQL)
      Complexity: ⭐⭐⭐⭐ Very High
      Effort: ⭐⭐⭐⭐ Very High
```

---

## Comparison Matrix

| Requirement | SQLite | RocksDB | git2-rs | JSONL | CQRS | RDF |
|---|---|---|---|---|---|---|
| **Relational queries** | ✅✅✅ | ❌ | ❌ | ❌ | ⚠️ | ✅✅ |
| **Write throughput** | ⚠️⚠️ | ✅✅✅ | ⚠️ | ✅✅✅ | ✅✅✅ | ❌ |
| **Single-file deployment** | ✅✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Version history** | ✅✅ | ✅ | ✅✅✅ | ✅✅✅ | ✅✅✅ | ✅✅ |
| **Audit trail** | ✅ | ❌ | ✅✅ | ✅✅✅ | ✅✅✅ | ⚠️ |
| **Offline-first** | ✅✅ | ✅✅✅ | ✅✅✅ | ✅✅✅ | ✅✅ | ❌ |
| **Collaboration** | ❌ | ❌ | ✅✅✅ | ⚠️ | ✅✅ | ✅✅ |
| **Semantic queries** | ⚠️ | ❌ | ❌ | ❌ | ✅✅ | ✅✅✅ |
| **Graph relationships** | ⚠️⚠️ | ❌ | ❌ | ❌ | ⚠️ | ✅✅✅ |
| **Time-travel queries** | ✅✅ | ⚠️ | ✅✅ | ✅ | ✅✅✅ | ⚠️ |
| **Merge conflicts** | ❌ | ❌ | ✅✅ | ⚠️ | ⚠️ | ❌ |
| **Learning curve** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Operational overhead** | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**Legend**: ✅✅✅ Excellent | ✅✅ Good | ✅ Okay | ⚠️ Possible but not ideal | ❌ Poor/Not suitable

---

## Architecture Patterns

### Pattern A: Simple Single-User (Recommended for MVP)

```
┌─ User edits in TUI
├─ Save to JSON file
├─ Compute changes
├─ Append to JSONL audit log
├─ Update SQLite index
└─ Done

Complexity: Low
Storage: ~/.wve/store/{slug}/
├─ worldview.json          (current state)
└─ audit.jsonl             (immutable log)

Database: ~/.wve/index.sqlite
├─ Table: worldviews       (search index)
└─ Table: worldview_versions (optional, for snapshots)
```

**When to use**:
- Single user or small team
- Offline-first usage
- Simple linear workflow
- Audit trail sufficient for compliance

**Trade-offs**:
- No merge conflict resolution
- Simple rollback (restore from version)
- No distributed collaboration

---

### Pattern B: Multi-Version with Snapshots (Recommended for v1.0)

```
┌─ User edits
├─ Compare with previous version
├─ Create semantic diff (json-patch)
├─ Save new version snapshot to SQLite
├─ Append audit entry (JSONL)
├─ Rebuild derived views (if needed)
└─ Done

Complexity: Medium
Storage:
├─ SQLite: worldview_versions table
│  ├─ version: Integer (1, 2, 3...)
│  ├─ data: JSON snapshot
│  ├─ created_at: Timestamp
│  └─ reason: String
└─ JSONL: audit.jsonl (optional, for compliance)

Key Features:
✅ Full history browsing
✅ Version comparison
✅ Time-travel queries
✅ Immutable audit log
❌ No merge support
```

**When to use**:
- Need full version history
- Compliance/audit requirements
- Small to medium-sized data
- Still single-writer

**Trade-offs**:
- Storage grows linearly (one full snapshot per version)
- Need periodic cleanup/compaction
- No distributed collaboration

---

### Pattern C: Hybrid Snapshots + Deltas (Recommended for Scale)

```
┌─ Every 100 versions
├─ Create full snapshot
└─ Mark as "anchor"

Between snapshots:
├─ Store only delta (json-patch)
├─ On access: load anchor + replay deltas
└─ Reduces storage ~80%

Complexity: Medium-High
Storage:
├─ SQLite
│  ├─ Table: worldview_versions
│  │  ├─ version: i64
│  │  ├─ anchor_version: Option<i64>
│  │  ├─ delta: JSON (RFC 6902)
│  │  └─ created_at: Timestamp
│  └─ Index: (worldview_id, version)
└─ Periodic cleanup of old deltas

Trade-offs:
⚠️ Access is O(n) from anchor (replay deltas)
✅ Storage ~80% reduction vs full snapshots
⚠️ Complexity of delta application
```

**When to use**:
- Thousands of versions per worldview
- Limited storage capacity
- Still single-writer
- Full history important

**Trade-offs**:
- Slower access to old versions (must replay)
- Complexity in code
- Delta corruption ruins everything after it

---

### Pattern D: Three-Way Merge (Multi-User Collaboration)

```
User A                  Shared Base              User B
  │                         │                      │
  ├─ Edit (yours)            │                      │
  │                           │                   ├─ Edit (theirs)
  │                           │                   │
  └─ Merge                    │                   │
      │                       │                   │
      └─ Load base ────────────┼──────────────────┼─ Load base
          Load yours                         Load theirs
          Load theirs ──────────────────────────┘

          Run 3-way merge(base, yours, theirs)
          │
          ├─ Same field: Auto-merge ✅
          ├─ Different fields: Auto-merge ✅
          ├─ Conflicting edits: Mark conflict ⚠️
          │
          └─ Return (merged, conflicts)

Complexity: High
Requires: threeway_merge crate
Conflict resolution: Manual or heuristic

Workflow:
1. User A makes changes
2. User B makes changes
3. On pull: Attempt 3-way merge
4. If conflicts: Show conflict UI
5. User resolves and commits
```

**When to use**:
- Multiple collaborators
- Distributed editing
- Need to merge independently-made changes

**Trade-offs**:
⚠️ Complex conflict scenarios
✅ Natural for Git-like workflows
❌ Doesn't work for all data types (beliefs, stances)

---

### Pattern E: Event Sourcing (Enterprise)

```
Command               Event Log              Projections
  │                      │                      │
  ├─ UpdateStance ──────→ StanceUpdated ───→ Read Model
  │                          │             (Current State)
  ├─ AddPoint ──────────→ PointAdded ───────→
  │                          │
  └─ ApplyEvidence ─→ EvidenceApplied ──→ Read Model
                             │
                        (Immutable log)

                        Can replay from beginning
                        to reconstruct any state

Complexity: Very High
Requirements:
✅ Event store (JSONL or DB)
✅ Event definitions
✅ Projections/handlers
✅ Snapshots (for performance)
✅ Event versioning

Benefits:
✅ Complete audit trail
✅ Event replay
✅ Time-travel queries
✅ Distributed systems friendly
✅ Works with CQRS pattern

Trade-offs:
❌ Significant complexity
❌ Learning curve steep
⚠️ Event schema evolution required
```

**When to use**:
- Complex business logic
- Full audit requirements
- Distributed systems
- Need event replay
- Advanced time-travel queries

---

### Pattern F: Temporal Property Graph (Advanced)

```
Entities:
┌─ Person (slug, name, interests)
├─ Worldview (subject, created_at)
├─ Belief/Point (theme, stance, confidence)
└─ Source (url, title, date)

Relationships (with timestamps):
├─ person → worldview (created_at)
├─ worldview → point (added_at, removed_at)
├─ point → source (cited_at)
├─ person → person (disagrees_with, influenced_by)
└─ worldview → worldview (evolved_from, supersedes)

Temporal Query Examples:
SELECT ?person ?stance ?date
WHERE {
  ?person wv:hasWorldview ?wv .
  ?wv wv:hasPoint ?p .
  ?p wv:stance ?stance .
  ?p dcterms:issued ?date .
  FILTER (?date <= "2025-01-15"^^xsd:dateTime)
}

Complexity: Very High
Technology: Neo4j or RDF triple store (Oxigraph)

Benefits:
✅ Semantic queries
✅ Relationship traversal
✅ Temporal constraints
✅ Complex reasoning

Trade-offs:
❌ Operational complexity
❌ Learning curve (SPARQL, Cypher)
❌ Large infrastructure needs
```

**When to use**:
- Analyzing belief relationships
- Comparing worldviews
- Finding consensus/disagreement patterns
- Long-term research/analysis

---

## Decision Table by Use Case

| Scenario | Recommended | Why | Roadmap |
|----------|-------------|-----|---------|
| **Personal belief journaling** | Pattern A | Simple, offline, audit trail | MVP |
| **Small group sharing** | Pattern A + invite system | Same but with sharing | MVP+ |
| **Compliance requirements** | Pattern B | Immutable audit log, snapshots | v1.0 |
| **Large histories (1000+ versions)** | Pattern C | Reduces storage | v1.2 |
| **Team collaboration** | Pattern D | Merge support, conflict resolution | v1.5 |
| **Full version control** | git2-rs | Branch, tag, distributed | v2.0 |
| **Complex reasoning/analysis** | Pattern F | Graph queries, relationships | v2.5+ |
| **High-load system** | RocksDB + CQRS | Write performance + event log | Enterprise |

---

## Implementation Roadmap

### Week 1-2 (MVP) - Pattern A
```
[] Add JSONL audit logging
[] Add --reason flag to all mutations
[] Add `history` command
[] Add `diff` command
[] Test with manual edits
```

### Week 3-4 (v1.0) - Pattern B
```
[] Add worldview_versions table
[] Implement version snapshots
[] Add version comparison UI
[] Add rollback capability
[] Document versioning workflow
```

### Week 5-6 (v1.2) - Pattern C (Optional, if needed)
```
[] Implement snapshot + delta storage
[] Add compaction logic
[] Benchmark storage savings
[] Add delta integrity checks
```

### Week 7-8 (v1.5) - Pattern D (If multi-user needed)
```
[] Add threeway_merge dependency
[] Implement merge logic
[] Add conflict detection UI
[] Add merge resolution commands
```

### Long-term (v2.0+) - Pattern E/F
```
[] Event sourcing foundation
[] CQRS read models
[] Temporal graph support
[] Or: git2-rs integration
```

---

## Crate Dependency Summary

### Essential (MVP)
```toml
serde_json = "1"
chrono = { version = "0.4", features = ["serde"] }
rusqlite = { version = "0.32", features = ["bundled"] }
uuid = { version = "1.0", features = ["v4", "serde"] }
```

### Phase 2 (v1.0)
```toml
# Already have: sqlite + chrono
# No new crates needed!
```

### Phase 3 (Diffs)
```toml
json-patch = "1.1"
```

### Phase 4 (Collaboration)
```toml
threeway_merge = "0.1"  # Git-style 3-way
# OR
deepmerge = "0.2"       # Policy-driven deep merge
# OR
automerge = "0.3"       # CRDT-based
```

### Phase 5 (Temporal)
```toml
# Uses existing dependencies
```

### Phase 6+ (Advanced)
```toml
git2 = "0.29"           # Full Git integration
rocksdb = "0.21"        # High-perf KV store
oxigraph = "0.4"        # RDF + SPARQL
```

---

## Storage Space Estimates

Based on single worldview with ~50 points:

```
Current JSON snapshot:   ~50 KB
Full version storage:
  10 versions:          ~500 KB (no cleanup)
  100 versions:         ~5 MB
  1000 versions:        ~50 MB

With snapshot + delta (every 10 versions):
  100 versions:         ~300 KB (snapshot at v0, 10, 20... + 9 deltas each)
  1000 versions:        ~3 MB

SQLite index:           ~100 KB per 100 worldviews

SQLite version table:   ~50 KB per 100 versions
```

---

## Testing Checklist

**Phase 1 (Audit)**:
- [ ] Audit entry round-trip serialization
- [ ] JSONL append doesn't corrupt
- [ ] Concurrent appends safe
- [ ] Change detection accurate

**Phase 2 (Versions)**:
- [ ] Version save/load roundtrip
- [ ] Version increments correctly
- [ ] Rollback produces original state
- [ ] Metadata preserved

**Phase 3 (Diffs)**:
- [ ] json-patch diff is reversible
- [ ] Patch applies correctly
- [ ] No data loss in patch
- [ ] Human display accurate

**Phase 4 (Merge)**:
- [ ] Non-overlapping changes auto-merge
- [ ] Overlapping changes detected
- [ ] Conflicts clearly marked
- [ ] Manual resolution works

**Phase 5 (Temporal)**:
- [ ] Time-travel query returns correct state
- [ ] Timeline query orders chronologically
- [ ] Empty time range handled
- [ ] Future dates handled

---

## References

See primary documents:
- `VERSIONED_STORAGE_RESEARCH.md` - Comprehensive research
- `VERSIONING_IMPLEMENTATION_GUIDE.md` - Code patterns and examples
