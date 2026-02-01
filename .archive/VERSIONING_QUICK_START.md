# Versioning Quick Start Card

One-page reference for implementing Phase 1 audit trail (2-3 hours).

## The Goal
Add immutable audit trail to track who changed what, when, why.

```
Before:  Save → Done
After:   Save → Log to JSONL → Done
```

## What Gets Created
```
~/.wve/store/{slug}/audit.jsonl

Example entry:
{"id":"550e8400-e29b-41d4-a716-446655440000","timestamp":"2025-02-01T14:30:00Z","operation":"update_points","user":"alice","wve_version":"0.8.0","reason":"Increased AI confidence based on research","before":{...},"after":{...},"changes":[{"path":"/points/0/confidence","op":"replace","old_value":0.7,"new_value":0.85}]}
```

## 4 Simple Changes

### 1. Add to Cargo.toml
```toml
uuid = { version = "1.0", features = ["v4", "serde"] }
```

### 2. Create src/storage/audit.rs
Copy from VERSIONING_IMPLEMENTATION_GUIDE.md, Section 1.1

**Key functions**:
- `struct AuditEntry` - What to log
- `append_audit_entry()` - Write to JSONL
- `get_audit_log()` - Read from JSONL
- `compute_changes()` - Detect what changed

### 3. Update src/storage/json_store.rs::save_worldview()
Copy from VERSIONING_IMPLEMENTATION_GUIDE.md, Section 1.2

**Changes**:
```rust
// Before
pub fn save_worldview(worldview: &Worldview) -> Result<PathBuf, StorageError> {
    let dir = get_worldview_dir(&worldview.slug);
    fs::create_dir_all(&dir)?;
    let file_path = dir.join("worldview.json");
    let json = serde_json::to_string_pretty(worldview)?;
    fs::write(&file_path, json)?;
    Ok(file_path)
}

// After
pub fn save_worldview(worldview: &Worldview) -> Result<PathBuf, StorageError> {
    let dir = get_worldview_dir(&worldview.slug);
    fs::create_dir_all(&dir)?;
    let file_path = dir.join("worldview.json");

    // NEW: Load previous for audit
    let before = load_worldview(&worldview.slug).ok();

    let json = serde_json::to_string_pretty(worldview)?;
    fs::write(&file_path, json)?;

    // NEW: Log audit entry
    if let Ok(before_data) = before {
        let user = std::env::var("USER").unwrap_or_else(|_| "unknown".to_string());
        let reason = std::env::var("WVE_REASON").unwrap_or_else(|_| "Manual edit".to_string());
        let changes = crate::storage::audit::compute_changes(&before_data, worldview);

        let entry = crate::storage::audit::AuditEntry {
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

        crate::storage::audit::append_audit_entry(&worldview.slug, &entry)?;
    }

    Ok(file_path)
}
```

### 4. Add history command to src/cli.rs
Copy from VERSIONING_IMPLEMENTATION_GUIDE.md, Section 1.3

**Usage**:
```bash
wve history my-slug              # Show all entries
wve history my-slug --limit 10   # Last 10 entries
wve history my-slug --json       # JSON output
```

## Testing (5 minutes)

```bash
# 1. Create a worldview
wve create "Test" --subject "AI"

# 2. Edit it manually
# Edit ~/.wve/store/test/worldview.json

# 3. View history
wve history test

# Output should show:
# 2025-02-01 12:34:56 - update by you (1 changes)
#   Reason: Manual edit
#     replace /points/0/stance: "cautious" → "very_cautious"
```

## Module Organization

**src/storage/mod.rs** needs to declare audit module:
```rust
pub mod audit;
pub mod db;
pub mod error;
pub mod json_store;
```

## That's It!

You now have:
- ✅ Immutable audit log
- ✅ Who/what/when/why tracking
- ✅ Commit message support (--reason flag)
- ✅ View command to browse history
- ✅ Semantic change detection

## Next Steps (Later)

**Phase 2** (1 week): Add versioning table for snapshots
- Compare any two versions
- Rollback capability
- Time-travel queries

See: STORAGE_DECISION_MATRIX.md for roadmap

## Environment Variables

Users can set these to customize behavior:

```bash
WVE_REASON="Changed based on new research"  # Reason for change
USER=alice                                   # Who's making change
```

Or add `--reason` flag to CLI:
```bash
wve edit my-slug --reason "Updated stance on AI safety"
```

## Troubleshooting

**Q: Where is audit.jsonl stored?**
A: `~/.wve/store/{slug}/audit.jsonl`

**Q: What if I make an edit without saving?**
A: No audit entry created (it's only on save)

**Q: Can I edit audit.jsonl directly?**
A: Not recommended (breaks immutability), but it's just JSON

**Q: Will this break existing worldviews?**
A: No, they continue working. First edit creates audit.jsonl.

## Summary

| Item | Time | Impact |
|------|------|--------|
| Add uuid dependency | 1 min | ✅ Needed |
| Create audit.rs | 10 min | ✅ Copy-paste |
| Update save_worldview() | 15 min | ✅ 10 lines |
| Add history command | 10 min | ✅ Copy-paste |
| Test | 5 min | ✅ Manual |
| Total | ~40 min | ✅ High value |

---

## Files to Reference

1. **Full instructions**: VERSIONING_IMPLEMENTATION_GUIDE.md (Phase 1)
2. **Code examples**: VERSIONED_STORAGE_RESEARCH.md (Section 4)
3. **Decision matrix**: STORAGE_DECISION_MATRIX.md
4. **Index**: VERSIONING_INDEX.md (full roadmap)

---

**Ready to implement?** Start with changing Cargo.toml, then work through the 4 steps above.

**Questions?** Check VERSIONING_IMPLEMENTATION_GUIDE.md Phase 1 for full context.
