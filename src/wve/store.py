"""Persistent storage for worldview extractions - beats-like pattern."""

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# Storage location
DEFAULT_STORE_DIR = Path.home() / ".wve" / "store"


class WorldviewEntry(BaseModel):
    """A stored worldview extraction."""

    slug: str
    display_name: str
    channel_url: str | None = None
    source_count: int = 0
    quote_count: int = 0
    themes: list[dict] = Field(default_factory=list)
    top_quotes: list[dict] = Field(default_factory=list)
    contrarian_quotes: list[dict] = Field(default_factory=list)
    report_path: str | None = None
    transcripts_dir: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list)


def get_store_dir() -> Path:
    """Get store directory, creating if needed."""
    store_dir = DEFAULT_STORE_DIR
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def get_index_path() -> Path:
    """Get path to the index file."""
    return get_store_dir() / "index.jsonl"


def get_entry_dir(slug: str) -> Path:
    """Get directory for a specific entry."""
    entry_dir = get_store_dir() / slug
    entry_dir.mkdir(parents=True, exist_ok=True)
    return entry_dir


def save_entry(entry: WorldviewEntry) -> Path:
    """Save a worldview entry."""
    entry.updated_at = datetime.now()
    entry_dir = get_entry_dir(entry.slug)
    entry_path = entry_dir / "worldview.json"
    entry_path.write_text(entry.model_dump_json(indent=2))
    
    # Append to index
    _update_index(entry)
    return entry_path


def _update_index(entry: WorldviewEntry) -> None:
    """Update or append entry in index."""
    index_path = get_index_path()
    entries = load_index()
    
    # Replace or append
    found = False
    for i, e in enumerate(entries):
        if e.slug == entry.slug:
            entries[i] = entry
            found = True
            break
    if not found:
        entries.append(entry)
    
    # Write back
    with open(index_path, "w") as f:
        for e in entries:
            f.write(e.model_dump_json() + "\n")


def load_entry(slug: str) -> WorldviewEntry:
    """Load a worldview entry."""
    entry_path = get_entry_dir(slug) / "worldview.json"
    if not entry_path.exists():
        raise FileNotFoundError(f"Entry not found: {slug}")
    return WorldviewEntry.model_validate_json(entry_path.read_text())


def load_index() -> list[WorldviewEntry]:
    """Load all entries from index."""
    index_path = get_index_path()
    if not index_path.exists():
        return []
    
    entries = []
    for line in index_path.read_text().strip().split("\n"):
        if line:
            try:
                entries.append(WorldviewEntry.model_validate_json(line))
            except Exception:
                continue
    return entries


def list_entries() -> list[WorldviewEntry]:
    """List all stored worldview entries."""
    return load_index()


def search_entries(query: str) -> list[WorldviewEntry]:
    """Search entries by name, slug, or tags."""
    query_lower = query.lower()
    results = []
    for entry in load_index():
        if (query_lower in entry.slug.lower() or
            query_lower in entry.display_name.lower() or
            any(query_lower in t.lower() for t in entry.tags)):
            results.append(entry)
    return results


def delete_entry(slug: str) -> bool:
    """Delete a worldview entry."""
    import shutil
    entry_dir = get_store_dir() / slug
    if entry_dir.exists():
        shutil.rmtree(entry_dir)
        # Update index
        entries = [e for e in load_index() if e.slug != slug]
        index_path = get_index_path()
        with open(index_path, "w") as f:
            for e in entries:
                f.write(e.model_dump_json() + "\n")
        return True
    return False
