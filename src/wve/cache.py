"""Content-hash based caching for wve artifacts."""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "wve"
DEFAULT_TTL_DAYS = 30


def get_cache_dir() -> Path:
    """Get cache directory from env or default."""
    cache_dir = os.environ.get("WVE_CACHE_DIR", str(DEFAULT_CACHE_DIR))
    return Path(cache_dir)


def content_hash(data: Any) -> str:
    """Generate SHA256 hash of data."""
    if isinstance(data, str):
        content = data
    else:
        content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def cache_key(prefix: str, *args: Any) -> str:
    """Generate cache key from prefix and arguments."""
    combined = json.dumps(args, sort_keys=True, default=str)
    return f"{prefix}_{content_hash(combined)}"


def get_cached(key: str, ttl_days: int = DEFAULT_TTL_DAYS) -> dict | None:
    """Retrieve cached artifact if exists and not expired."""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / f"{key}.json"

    if not cache_file.exists():
        return None

    # Check TTL
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    if datetime.now() - mtime > timedelta(days=ttl_days):
        cache_file.unlink()
        return None

    try:
        with open(cache_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def set_cached(key: str, data: dict) -> Path:
    """Store artifact in cache."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / f"{key}.json"
    with open(cache_file, "w") as f:
        json.dump(data, f, default=str)

    return cache_file


def clear_cache(older_than_days: int | None = None) -> int:
    """Clear cache files, optionally only older than N days.

    Returns number of files deleted.
    """
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        return 0

    deleted = 0
    cutoff = datetime.now() - timedelta(days=older_than_days) if older_than_days else None

    for cache_file in cache_dir.glob("*.json"):
        if cutoff:
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if mtime > cutoff:
                continue
        cache_file.unlink()
        deleted += 1

    return deleted


def cache_stats() -> dict:
    """Get cache statistics."""
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        return {"files": 0, "size_bytes": 0, "oldest": None, "newest": None}

    files = list(cache_dir.glob("*.json"))
    if not files:
        return {"files": 0, "size_bytes": 0, "oldest": None, "newest": None}

    total_size = sum(f.stat().st_size for f in files)
    mtimes = [datetime.fromtimestamp(f.stat().st_mtime) for f in files]

    return {
        "files": len(files),
        "size_bytes": total_size,
        "oldest": min(mtimes).isoformat() if mtimes else None,
        "newest": max(mtimes).isoformat() if mtimes else None,
    }
