# Versioning Research & Implementation Index

Complete guide to professional-grade versioned storage for Weave.

## Start Here

**New to this research?** Read in this order:

1. **[RESEARCH_SUMMARY.md](./RESEARCH_SUMMARY.md)** (15 min read)
   - Executive summary
   - Key findings
   - Recommended path
   - Architecture diagrams
   - Quick start guide

2. **[STORAGE_DECISION_MATRIX.md](./STORAGE_DECISION_MATRIX.md)** (10 min read)
   - Decision tree
   - Comparison matrix
   - Implementation roadmap
   - Use case routing

3. **[VERSIONED_STORAGE_RESEARCH.md](./VERSIONED_STORAGE_RESEARCH.md)** (Reference)
   - Deep dive on all 6 topics
   - Code examples
   - Crate evaluations
   - Technical details

4. **[VERSIONING_IMPLEMENTATION_GUIDE.md](./VERSIONING_IMPLEMENTATION_GUIDE.md)** (Implementation)
   - Phase 1-5 code
   - Ready to copy-paste
   - Integration steps
   - Testing strategies

---

## Document Guide

### RESEARCH_SUMMARY.md
**Purpose**: Executive overview and decision framework

**Contains**:
- Summary of all 6 research areas
- Recommended architecture (SQLite + JSONL)
- Implementation roadmap (MVP → Enterprise)
- Crate recommendations
- Security & performance analysis
- Quick start instructions

**Read when**: First time, need overview, deciding what to implement

**Length**: ~3000 words

---

### STORAGE_DECISION_MATRIX.md
**Purpose**: Quick reference and routing tool

**Contains**:
- Decision tree (START → recommended approach)
- Comparison matrix (6 architectures × 12 dimensions)
- 6 detailed patterns (A-F) with pros/cons
- Use case routing table
- Phase-by-phase roadmap
- Crate dependency summary
- Storage space estimates
- Testing checklist

**Read when**: Need to pick a pattern, estimate effort, plan roadmap

**Quick sections**:
```
├─ Decision Tree (2 min)
├─ Comparison Matrix (5 min)
├─ Architecture Patterns (10 min)
├─ Roadmap (5 min)
└─ References to docs
```

**Length**: ~2500 words

---

### VERSIONED_STORAGE_RESEARCH.md
**Purpose**: Comprehensive technical reference

**Sections**:
1. **Versioning Strategies** (800 words)
   - Content-addressable storage
   - Snapshots vs deltas
   - Hybrid approach
   - Time-travel queries

2. **Storage Backends** (1200 words)
   - SQLite + schema versioning
   - RocksDB characteristics
   - git2-rs embedding
   - JSONL audit logs
   - Comparison table

3. **Diffing Strategies** (1500 words)
   - json-patch (RFC 6902)
   - jsondiffpatch library
   - Semantic diffing for worldviews
   - Three-way merge algorithms
   - Conflict resolution

4. **Audit Trails** (800 words)
   - Immutable logs
   - User tracking
   - Rollback capabilities
   - Event sourcing pattern

5. **Migration & Compatibility** (600 words)
   - Schema migrations
   - Backward compatibility
   - Data export
   - Version-on-load pattern

6. **Graph Versioning** (1000 words)
   - Temporal graphs
   - RDF triple stores
   - Property graphs
   - Temporal queries

**Read when**: Need deep understanding of a topic, implementing a specific phase

**Code examples**: 60+ working code samples

**Length**: ~7000 words

---

### VERSIONING_IMPLEMENTATION_GUIDE.md
**Purpose**: Step-by-step integration guide

**Phases**:

**Phase 1: Audit Trail** (2-3 hours)
- Audit entry structs
- JSONL appending
- Semantic change detection
- History CLI command

**Phase 2: Snapshots** (1 week)
- SQLite versioning table
- Version save/load
- Version comparison
- Rollback command

**Phase 3: Compact Storage** (3-4 days)
- Snapshot + delta hybrid
- Anchor points
- Delta replay

**Phase 4: Collaboration** (1-2 weeks)
- Three-way merge
- Conflict detection
- Merge resolution UI

**Phase 5: Temporal Queries** (Low effort)
- Query as-of timestamp
- Timeline generation

**Read when**: Ready to implement, need actual code

**Code status**: All examples copy-paste ready

**Length**: ~3500 words + code

---

## Quick Navigation

### By Question

**"Should I use SQLite or RocksDB?"**
→ STORAGE_DECISION_MATRIX.md → Comparison Matrix

**"How do I show changes between versions?"**
→ VERSIONED_STORAGE_RESEARCH.md → Section 3 (Diffing)
→ VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 3

**"What if two users edit the same worldview?"**
→ STORAGE_DECISION_MATRIX.md → Pattern D (Three-Way Merge)
→ VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 4

**"How do I query what Alice believed on Jan 15?"**
→ VERSIONED_STORAGE_RESEARCH.md → Section 1.4 (Time-Travel)
→ VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 5

**"What's the storage overhead?"**
→ STORAGE_DECISION_MATRIX.md → Storage Space Estimates
→ VERSIONED_STORAGE_RESEARCH.md → Section 2.1/2.2

**"What crates should I add to Cargo.toml?"**
→ RESEARCH_SUMMARY.md → Crate Recommendations
→ STORAGE_DECISION_MATRIX.md → Crate Dependency Summary

---

### By Implementation Phase

**MVP (Current)**
- Read: RESEARCH_SUMMARY.md (overview)
- Read: STORAGE_DECISION_MATRIX.md (Pattern A)
- Keep: Current code, add audit trail in Phase 1

**Phase 1: Audit Trail (2-3 days)**
- Read: VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 1
- Code: Copy audit.rs, update json_store.rs, add history command
- Test: Manual edits, verify history output
- Document: Update CLI help

**Phase 2: Snapshots (1 week)**
- Read: STORAGE_DECISION_MATRIX.md → Pattern B
- Read: VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 2
- Code: Add versioning.rs, SQLite migration, diff command
- Test: Version save/load/rollback, time-travel queries

**Phase 3+: Advanced**
- Read: STORAGE_DECISION_MATRIX.md → Pattern C-F
- Read: RESEARCH_SUMMARY.md → "Long-term" section
- Choose: Which pattern fits your needs
- Implement: Following VERSIONING_IMPLEMENTATION_GUIDE.md

---

### By Technology

**SQLite Schema Versioning**
- RESEARCH_SUMMARY.md → "Storage Backends"
- VERSIONED_STORAGE_RESEARCH.md → Section 2.1
- VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 2

**JSON Diffing**
- VERSIONED_STORAGE_RESEARCH.md → Section 3.1 (libraries)
- VERSIONED_STORAGE_RESEARCH.md → Section 3.2 (semantic)
- VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 3 code

**Three-Way Merge**
- VERSIONED_STORAGE_RESEARCH.md → Section 3.3
- VERSIONING_IMPLEMENTATION_GUIDE.md → Phase 4
- Code example: `merge_worldviews()` function

**Event Sourcing**
- RESEARCH_SUMMARY.md → Advanced options
- VERSIONED_STORAGE_RESEARCH.md → Section 4 (Audit Trails)
- STORAGE_DECISION_MATRIX.md → Pattern E (Event Sourcing)

**Temporal Graphs**
- VERSIONED_STORAGE_RESEARCH.md → Section 6
- STORAGE_DECISION_MATRIX.md → Pattern F
- Code: RDF/SPARQL examples

**git2-rs Integration**
- VERSIONED_STORAGE_RESEARCH.md → Section 2.3
- STORAGE_DECISION_MATRIX.md → Pattern (git2-rs specific)
- Roadmap: v2.0+ (long-term)

---

## Key Decisions Made

### Architecture Choice: SQLite + JSONL

**Why this?**
- ✅ Portable (single .db file)
- ✅ Offline-first
- ✅ ACID transactions
- ✅ FTS5 full-text search
- ✅ No server needed
- ✅ Standard (developers know SQL)
- ✅ Immutable audit log (JSONL)

**Why not alternatives?**
- ❌ RocksDB: Overkill, no query language
- ❌ git2-rs: Too heavy for now, adds complexity
- ❌ Custom: Reinventing the wheel

---

### Diffing Choice: json-patch + Semantic

**Why?**
- ✅ RFC 6902 standard format
- ✅ Reversible (patch + reverse = identity)
- ✅ Compact encoding
- ✅ Works with serde_json out-of-box
- ✅ Semantic diffs for user display
- ✅ Migration path to deeper analysis

---

### Audit Trail Choice: JSONL

**Why?**
- ✅ Immutable by design (append-only)
- ✅ Survives schema migrations
- ✅ Git-friendly (diffs work)
- ✅ Grep/jq work natively
- ✅ No database dependency
- ✅ Portable text format
- ✅ Zero complexity

---

## Timeline Estimates

```
Phase 1 (Audit):           2-3 days    (HIGH priority)
Phase 2 (Snapshots):       1 week      (HIGH priority)
Phase 3 (Delta storage):   3-4 days    (LOW priority, only if needed)
Phase 4 (Collaboration):   1-2 weeks   (MEDIUM priority, if multi-user)
Phase 5 (Temporal):        2-3 days    (Built-in after Phase 2)
Phase 6+ (Advanced):       3-4+ weeks  (FUTURE, when scaling)

MVP target:      Phase 1 + 2 = ~2 weeks
v1.0 release:    Phase 1 + 2 = v1.0
v1.2 (optional): + Phase 3 = additional storage optimization
v1.5+ (future):  Collaboration, advanced features
```

---

## File Organization

Current codebase:
```
weave/
├─ VERSIONING_INDEX.md              (this file)
├─ RESEARCH_SUMMARY.md              (overview & quick start)
├─ STORAGE_DECISION_MATRIX.md       (patterns & routing)
├─ VERSIONED_STORAGE_RESEARCH.md    (comprehensive reference)
├─ VERSIONING_IMPLEMENTATION_GUIDE.md (copy-paste code)
├─ src/
│  ├─ storage/
│  │  ├─ mod.rs
│  │  ├─ db.rs                      (existing: SQLite metadata)
│  │  ├─ json_store.rs              (existing: worldview persistence)
│  │  ├─ error.rs
│  │  ├─ audit.rs                   (NEW: Phase 1)
│  │  └─ versioning.rs              (NEW: Phase 2)
│  ├─ comparison/
│  │  ├─ mod.rs
│  │  ├─ diff.rs                    (UPDATE: Phase 3)
│  │  └─ merge.rs                   (NEW: Phase 4)
│  └─ cli.rs                        (UPDATE: Add commands)
└─ Cargo.toml                       (ADD: uuid, json-patch, etc)
```

---

## Implementation Checklist

### Before Starting
- [ ] Read RESEARCH_SUMMARY.md
- [ ] Review STORAGE_DECISION_MATRIX.md
- [ ] Understand current storage (json_store.rs + db.rs)
- [ ] Confirm Phase 1 is priority

### Phase 1: Audit Trail
- [ ] Add uuid to Cargo.toml
- [ ] Create src/storage/audit.rs (from guide)
- [ ] Update src/storage/json_store.rs::save_worldview()
- [ ] Add history command to CLI
- [ ] Test: Create, edit, view history
- [ ] Document in CHANGELOG

### Phase 2: Snapshots
- [ ] Create SQLite migration script
- [ ] Create src/storage/versioning.rs
- [ ] Add version table queries
- [ ] Add diff display functions
- [ ] Add version/rollback commands
- [ ] Test: Version save/load/compare
- [ ] Document in CHANGELOG

### Phase 3+: Future
- [ ] Decide if needed based on usage
- [ ] Schedule accordingly
- [ ] Follow STORAGE_DECISION_MATRIX.md guidance

---

## References & Links

**Rust Crates Used**:
- [uuid](https://crates.io/crates/uuid)
- [json-patch](https://crates.io/crates/json-patch)
- [threeway_merge](https://crates.io/crates/threeway_merge)
- [rusqlite_migration](https://crates.io/crates/rusqlite_migration)
- [chrono](https://crates.io/crates/chrono)

**Standards**:
- [RFC 6902 - JSON Patch](https://tools.ietf.org/html/rfc6902)
- [RFC 7396 - JSON Merge Patch](https://tools.ietf.org/html/rfc7396)
- [ISO 8601 - Date/Time Format](https://www.iso.org/iso-8601-date-and-time-format.html)

**Background Reading**:
- [Git Internals - Content-Addressable Storage](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)

---

## Support & Questions

### For implementation questions:
- See VERSIONING_IMPLEMENTATION_GUIDE.md
- Check code examples in VERSIONED_STORAGE_RESEARCH.md
- Review integration checklist above

### For architecture questions:
- See STORAGE_DECISION_MATRIX.md decision tree
- Compare patterns section for trade-offs
- Check roadmap for sequencing

### For specific technology:
- Search document index by technology name
- Check crate recommendations in relevant section

---

## Research Metadata

**Research Date**: 2026-02-01
**Status**: Complete and ready for implementation
**Scope**: All 6 research areas (versioning, storage, diffing, audit, migration, graphs)
**Code Status**: All examples tested and ready to integrate
**Coverage**: MVP through Enterprise architecture

**Documentation Quality**:
- 4 complementary documents
- 15,000+ words
- 60+ code examples
- Decision matrices
- Roadmaps
- Implementation guides

**Next Step**: Choose Phase 1 implementation or advance to Phase 2 based on priorities.
