"""Classification heuristics for video candidates (v0.2)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from wve.identity import Identity


class VideoCandidate(BaseModel):
    """A video candidate from search results."""

    id: str
    title: str
    channel: str
    channel_id: str
    duration_seconds: int
    url: str
    published: datetime

    # Classification
    classification: Literal["likely", "uncertain", "false_positive"] | None = None
    classification_reason: str | None = None
    confidence: float = 0.0

    # User decision
    confirmed: bool | None = None
    rejected: bool | None = None


class CandidateSet(BaseModel):
    """A set of video candidates from a search."""

    query: str
    identity_slug: str | None = None
    candidates: list[VideoCandidate] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


# Entertainment/music channels - common false positive sources
ENTERTAINMENT_INDICATORS = [
    "cover", "reaction", "music video", "official video", "lyrics",
    "karaoke", "remix", "parody", "trailer", "movie clip", "scene",
    "gameplay", "walkthrough", "let's play", "stream highlights",
]

# Interview/podcast format indicators
INTERVIEW_INDICATORS = [
    "interview", "podcast", "conversation", "talks with", "featuring",
    "guest", "episode", "ep.", "ep ", "#", "with special guest",
    "fireside chat", "keynote", "panel", "q&a", "ama",
]


def classify_candidate(
    candidate: VideoCandidate,
    query: str,
    identity: Identity | None = None,
) -> tuple[Literal["likely", "uncertain", "false_positive"], str, float]:
    """
    Classify a video candidate.
    
    Returns (classification, reason, confidence).
    """
    title_lower = candidate.title.lower()
    query_lower = query.lower()
    query_parts = query_lower.split()

    # Check against identity's known data
    if identity:
        # From subject's own channel - highest confidence
        channel_ids = [c.id for c in identity.channels]
        if candidate.channel_id in channel_ids or any(
            c.id.lower() in candidate.channel.lower() for c in identity.channels
        ):
            return ("likely", "from subject's own channel", 0.99)

        # From trusted channel
        if candidate.channel_id in identity.trusted_channels:
            return ("likely", "from trusted channel", 0.95)

        # Previously confirmed
        if candidate.id in identity.confirmed_videos:
            return ("likely", "previously confirmed", 1.0)

        # Previously rejected
        if candidate.id in identity.rejected_videos:
            return ("false_positive", "previously rejected", 1.0)

        # Matches suspicious pattern
        for pattern in identity.suspicious_patterns:
            if pattern.lower() in title_lower:
                return ("false_positive", f"matches suspicious pattern: {pattern}", 0.7)

    # Full name in title - strong signal
    if query_lower in title_lower:
        return ("likely", "full name in title", 0.85)

    # All name parts in title
    if all(part in title_lower for part in query_parts):
        # Check for entertainment false positives
        for indicator in ENTERTAINMENT_INDICATORS:
            if indicator in title_lower:
                return ("false_positive", f"entertainment content ({indicator})", 0.8)
        return ("likely", "all name parts in title", 0.75)

    # Interview/podcast format with partial match
    has_interview_indicator = any(ind in title_lower for ind in INTERVIEW_INDICATORS)
    has_partial_match = any(part in title_lower for part in query_parts)

    if has_interview_indicator and has_partial_match:
        return ("uncertain", "interview format with partial name match", 0.5)

    # Partial match only - uncertain
    if has_partial_match:
        # Check for entertainment first
        for indicator in ENTERTAINMENT_INDICATORS:
            if indicator in title_lower:
                return ("false_positive", f"entertainment content ({indicator})", 0.8)
        return ("uncertain", "partial name match only", 0.3)

    # No meaningful match
    return ("false_positive", "no name match in title", 0.9)


def classify_candidates(
    candidates: list[VideoCandidate],
    query: str,
    identity: Identity | None = None,
) -> list[VideoCandidate]:
    """Classify all candidates in a list."""
    for candidate in candidates:
        classification, reason, confidence = classify_candidate(
            candidate, query, identity
        )
        candidate.classification = classification
        candidate.classification_reason = reason
        candidate.confidence = confidence
    return candidates


def update_identity_from_feedback(
    identity: Identity,
    candidate: VideoCandidate,
    confirmed: bool,
) -> None:
    """Update identity heuristics based on user confirmation."""
    if confirmed:
        if candidate.id not in identity.confirmed_videos:
            identity.confirmed_videos.append(candidate.id)

        # Remove from rejected if present
        if candidate.id in identity.rejected_videos:
            identity.rejected_videos.remove(candidate.id)

        # Trust this channel more after multiple confirmations
        if candidate.channel_id not in identity.trusted_channels:
            confirmed_from_channel = sum(
                1 for vid_id in identity.confirmed_videos
                # We don't have channel info for all videos, so just count
                # This is a simplified heuristic
            )
            # After 3+ confirmed videos, we could add trust
            # But we need channel tracking - defer to future enhancement
    else:
        if candidate.id not in identity.rejected_videos:
            identity.rejected_videos.append(candidate.id)

        # Remove from confirmed if present
        if candidate.id in identity.confirmed_videos:
            identity.confirmed_videos.remove(candidate.id)

        # Learn suspicious patterns from title
        # For now, just track rejections; pattern learning is complex
