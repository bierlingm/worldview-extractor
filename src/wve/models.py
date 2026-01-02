"""Pydantic data models for wve."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    """Metadata for a discovered video."""

    id: str
    title: str
    channel: str
    channel_id: str
    duration_seconds: int
    url: str
    published: datetime


class TranscriptManifest(BaseModel):
    """Manifest linking videos to their transcript files."""

    created_at: datetime = Field(default_factory=datetime.now)
    videos: list[VideoMetadata]
    transcripts: dict[str, Path]  # video_id -> file path


class ExtractedKeyword(BaseModel):
    """A keyword extracted from transcripts."""

    term: str
    score: float
    frequency: int
    sources: list[str]  # video_ids


class ExtractedEntity(BaseModel):
    """A named entity extracted from transcripts."""

    text: str
    label: str  # PERSON, ORG, GPE, etc.
    frequency: int = 1
    sources: list[str] = Field(default_factory=list)


class ExtractedPhrase(BaseModel):
    """An n-gram phrase extracted from transcripts."""

    phrase: str
    count: int
    sources: list[str]


class TfidfTerm(BaseModel):
    """A term with its TF-IDF score."""

    term: str
    score: float


class CoOccurrence(BaseModel):
    """A pair of terms that co-occur frequently."""

    pair: tuple[str, str]
    count: int


class Extraction(BaseModel):
    """Combined extraction results from all methods."""

    keywords: list[ExtractedKeyword] = Field(default_factory=list)
    entities: dict[str, list[ExtractedEntity]] = Field(default_factory=dict)
    phrases: list[ExtractedPhrase] = Field(default_factory=list)
    tfidf: list[TfidfTerm] = Field(default_factory=list)
    co_occurrences: list[CoOccurrence] = Field(default_factory=list)
    source_transcripts: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class ClusterMember(BaseModel):
    """A term belonging to a cluster."""

    term: str
    distance: float


class Cluster(BaseModel):
    """A thematic cluster of related terms."""

    id: int
    label: str
    centroid_terms: list[str]
    members: list[ClusterMember]
    coherence: float


class ClusterResult(BaseModel):
    """Results from clustering extracted terms."""

    clusters: list[Cluster]
    unclustered: list[str] = Field(default_factory=list)
    silhouette_score: float
    embedding_model: str = "all-MiniLM-L6-v2"
    created_at: datetime = Field(default_factory=datetime.now)


class WorldviewPoint(BaseModel):
    """A single point in someone's worldview."""

    point: str
    elaboration: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    sources: list[str]


class Worldview(BaseModel):
    """Synthesized worldview from extracted themes."""

    subject: str
    points: list[WorldviewPoint]
    method: str  # quick, medium, deep
    depth: str
    generated_at: datetime = Field(default_factory=datetime.now)
    source_videos: list[str]


class SearchResult(BaseModel):
    """Results from video search."""

    query: str
    max_results: int
    videos: list[VideoMetadata]
    created_at: datetime = Field(default_factory=datetime.now)
