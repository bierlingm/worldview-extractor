"""Identity management for v0.2 - tracks subjects and their confirmed/rejected videos."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# Default storage location
DEFAULT_IDENTITY_DIR = Path.home() / ".wve" / "identities"


class Channel(BaseModel):
    """A YouTube/video channel belonging to a subject."""

    platform: Literal["youtube", "vimeo", "rumble"] = "youtube"
    id: str
    url: str
    name: str | None = None
    verified: bool = False


class Identity(BaseModel):
    """A subject's identity profile with their channels and confirmed content."""

    slug: str
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)
    websites: list[str] = Field(default_factory=list)
    confirmed_videos: list[str] = Field(default_factory=list)  # video IDs
    rejected_videos: list[str] = Field(default_factory=list)  # video IDs
    trusted_channels: list[str] = Field(default_factory=list)  # channel IDs
    suspicious_patterns: list[str] = Field(default_factory=list)  # title patterns
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


def slugify(name: str) -> str:
    """Convert a display name to a slug."""
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def get_identity_dir() -> Path:
    """Get the identity storage directory, creating if needed."""
    identity_dir = DEFAULT_IDENTITY_DIR
    identity_dir.mkdir(parents=True, exist_ok=True)
    return identity_dir


def get_identity_path(slug: str) -> Path:
    """Get the path to an identity file."""
    return get_identity_dir() / f"{slug}.json"


def identity_exists(slug: str) -> bool:
    """Check if an identity exists."""
    return get_identity_path(slug).exists()


def save_identity(identity: Identity) -> Path:
    """Save an identity to disk."""
    identity.updated_at = datetime.now()
    path = get_identity_path(identity.slug)
    path.write_text(identity.model_dump_json(indent=2))
    return path


def load_identity(slug: str) -> Identity:
    """Load an identity from disk."""
    path = get_identity_path(slug)
    if not path.exists():
        raise FileNotFoundError(f"Identity not found: {slug}")
    return Identity.model_validate_json(path.read_text())


def list_identities() -> list[Identity]:
    """List all stored identities."""
    identity_dir = get_identity_dir()
    identities = []
    for path in sorted(identity_dir.glob("*.json")):
        try:
            identities.append(Identity.model_validate_json(path.read_text()))
        except Exception:
            continue
    return identities


def delete_identity(slug: str) -> bool:
    """Delete an identity."""
    path = get_identity_path(slug)
    if path.exists():
        path.unlink()
        return True
    return False


def create_identity(
    display_name: str,
    slug: str | None = None,
    aliases: list[str] | None = None,
    channel_url: str | None = None,
    website: str | None = None,
) -> Identity:
    """Create a new identity profile."""
    slug = slug or slugify(display_name)

    if identity_exists(slug):
        raise ValueError(f"Identity already exists: {slug}")

    identity = Identity(
        slug=slug,
        display_name=display_name,
        aliases=aliases or [],
        websites=[website] if website else [],
    )

    if channel_url:
        channel = parse_channel_url(channel_url)
        identity.channels.append(channel)

    save_identity(identity)
    return identity


def parse_channel_url(url: str) -> Channel:
    """Parse a channel URL into a Channel object."""
    # YouTube patterns
    patterns = [
        (r"youtube\.com/@([^/?\s]+)", "youtube"),
        (r"youtube\.com/channel/([^/?\s]+)", "youtube"),
        (r"youtube\.com/c/([^/?\s]+)", "youtube"),
        (r"youtube\.com/user/([^/?\s]+)", "youtube"),
    ]

    for pattern, platform in patterns:
        match = re.search(pattern, url)
        if match:
            channel_id = match.group(1)
            return Channel(
                platform=platform,
                id=channel_id,
                url=url,
            )

    # Fallback: use URL as ID
    return Channel(
        platform="youtube",
        id=url,
        url=url,
    )


def add_channel_to_identity(slug: str, channel_url: str) -> Identity:
    """Add a channel to an existing identity."""
    identity = load_identity(slug)
    channel = parse_channel_url(channel_url)

    # Check for duplicates
    for existing in identity.channels:
        if existing.url == channel.url or existing.id == channel.id:
            raise ValueError(f"Channel already exists: {channel_url}")

    identity.channels.append(channel)
    save_identity(identity)
    return identity


def add_video_to_identity(slug: str, video_id: str, confirmed: bool = True) -> Identity:
    """Add a confirmed or rejected video to an identity."""
    identity = load_identity(slug)

    if confirmed:
        if video_id not in identity.confirmed_videos:
            identity.confirmed_videos.append(video_id)
        # Remove from rejected if present
        if video_id in identity.rejected_videos:
            identity.rejected_videos.remove(video_id)
    else:
        if video_id not in identity.rejected_videos:
            identity.rejected_videos.append(video_id)
        # Remove from confirmed if present
        if video_id in identity.confirmed_videos:
            identity.confirmed_videos.remove(video_id)

    save_identity(identity)
    return identity


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from URL or return as-is."""
    patterns = [
        r"youtube\.com/watch\?v=([^&\s]+)",
        r"youtu\.be/([^?\s]+)",
        r"youtube\.com/embed/([^?\s]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return url_or_id  # Assume it's already an ID
