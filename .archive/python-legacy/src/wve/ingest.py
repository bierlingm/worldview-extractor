"""Unified input ingestion layer for arbitrary text sources.

Supports:
- YouTube videos
- Substack articles
- Twitter/X threads
- Markdown files (blog posts, notes)
- PDF documents
- Plain text files

Auto-detects format and extracts content into normalized Source objects.
"""

import json
import re
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from wve.transcripts import download_transcript


class Source(BaseModel):
    """A textual source to be woven into worldview."""

    source_id: str
    source_type: Literal["video", "article", "tweet", "book", "podcast", "unknown"]
    text: str
    metadata: dict = Field(default_factory=dict)
    raw_format: str  # "youtube", "substack", "twitter", "markdown", "pdf", "text"
    ingested_at: datetime = Field(default_factory=datetime.now)

    def __hash__(self):
        """Make Source hashable."""
        return hash(self.source_id)


class Ingester(ABC):
    """Abstract base class for all source ingesters."""

    @abstractmethod
    def can_ingest(self, input_str: str | Path) -> bool:
        """Check if this ingester can handle the input.

        Args:
            input_str: URL, file path, or raw content

        Returns:
            True if this ingester can handle the input
        """
        pass

    @abstractmethod
    def ingest(self, input_str: str | Path) -> list[Source]:
        """Ingest the input and return list of Source objects.

        Args:
            input_str: URL, file path, or raw content

        Returns:
            List of Source objects extracted from input
        """
        pass


class YouTubeIngester(Ingester):
    """Ingest from YouTube videos."""

    def can_ingest(self, input_str: str | Path) -> bool:
        """Check if input is a YouTube URL."""
        if isinstance(input_str, Path):
            return False
        url_str = str(input_str).lower()
        return any(
            domain in url_str
            for domain in ["youtube.com", "youtu.be", "youtube-nocookie.com"]
        )

    def ingest(self, input_str: str | Path) -> list[Source]:
        """Download transcript from YouTube video."""
        if isinstance(input_str, Path):
            return []

        url = str(input_str)

        # Extract video ID
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[-1].split("?")[0]
        elif "youtube.com/watch" in url:
            video_id = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
            if not video_id:
                return []
            video_id = video_id.group(1)
        else:
            return []

        try:
            transcript_text = download_transcript(video_id)
            return [
                Source(
                    source_id=video_id,
                    source_type="video",
                    text=transcript_text,
                    metadata={
                        "url": url,
                        "video_id": video_id,
                        "platform": "youtube",
                    },
                    raw_format="youtube",
                )
            ]
        except Exception as e:
            return []


class SubstackIngester(Ingester):
    """Ingest from Substack articles."""

    def can_ingest(self, input_str: str | Path) -> bool:
        """Check if input is a Substack URL."""
        if isinstance(input_str, Path):
            return False
        url_str = str(input_str).lower()
        return "substack.com" in url_str

    def ingest(self, input_str: str | Path) -> list[Source]:
        """Extract content from Substack article."""
        if isinstance(input_str, Path):
            return []

        url = str(input_str)

        try:
            # Try to use curl to fetch the page
            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True,
                text=True,
                timeout=10,
            )

            html = result.stdout
            if not html:
                return []

            # Extract article title from og:title meta tag
            title_match = re.search(r'<meta property="og:title" content="([^"]*)"', html)
            title = title_match.group(1) if title_match else "Substack Article"

            # Simple extraction: get text between <article> tags or main content
            content_match = re.search(
                r'<div class="[^"]*article-content[^"]*">(.+?)</div>',
                html,
                re.DOTALL,
            )
            if content_match:
                content_html = content_match.group(1)
            else:
                # Fallback: extract text between common content markers
                content_html = html

            # Remove HTML tags
            text = re.sub(r"<[^>]+>", "\n", content_html)
            # Decode HTML entities
            text = (
                text.replace("&quot;", '"')
                .replace("&apos;", "'")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
            )
            # Clean up whitespace
            text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

            if not text:
                return []

            # Extract source ID from URL
            source_id = url.split("/")[-1].split("?")[0] or "substack-article"

            return [
                Source(
                    source_id=source_id,
                    source_type="article",
                    text=text,
                    metadata={
                        "url": url,
                        "title": title,
                        "platform": "substack",
                    },
                    raw_format="substack",
                )
            ]
        except Exception as e:
            return []


class TwitterIngester(Ingester):
    """Ingest from Twitter/X threads."""

    def can_ingest(self, input_str: str | Path) -> bool:
        """Check if input is a Twitter/X URL."""
        if isinstance(input_str, Path):
            return False
        url_str = str(input_str).lower()
        return any(
            domain in url_str for domain in ["twitter.com", "x.com", "t.co"]
        )

    def ingest(self, input_str: str | Path) -> list[Source]:
        """Extract tweets from Twitter/X thread.

        Note: This is a simplified implementation.
        In production, use the Twitter API or a specialized library.
        """
        if isinstance(input_str, Path):
            return []

        url = str(input_str)

        # For now, return a placeholder since direct scraping is complex
        # In production, use tweepy or other Twitter API clients
        source_id = url.split("/")[-1].split("?")[0] or "twitter-thread"

        return [
            Source(
                source_id=source_id,
                source_type="tweet",
                text="[Twitter thread content requires authentication - use Twitter API]",
                metadata={"url": url, "platform": "twitter"},
                raw_format="twitter",
            )
        ]


class MarkdownIngester(Ingester):
    """Ingest from Markdown files (blog posts, notes)."""

    def can_ingest(self, input_str: str | Path) -> bool:
        """Check if input is a markdown file."""
        path = Path(input_str)
        return path.exists() and path.suffix.lower() in [".md", ".markdown"]

    def ingest(self, input_str: str | Path) -> list[Source]:
        """Extract content from markdown file."""
        path = Path(input_str)
        if not path.exists():
            return []

        try:
            content = path.read_text(encoding="utf-8")

            # Extract title from first h1 or filename
            title_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else path.stem

            # Extract YAML frontmatter if present
            metadata = {"title": title, "file": str(path), "platform": "markdown"}
            if content.startswith("---"):
                fm_match = re.match(
                    r"---\n(.*?)\n---", content, re.DOTALL
                )
                if fm_match:
                    fm_text = fm_match.group(1)
                    # Parse YAML-like frontmatter
                    for line in fm_text.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()

            return [
                Source(
                    source_id=path.stem,
                    source_type="article",
                    text=content,
                    metadata=metadata,
                    raw_format="markdown",
                )
            ]
        except Exception as e:
            return []


class PDFIngester(Ingester):
    """Ingest from PDF files."""

    def can_ingest(self, input_str: str | Path) -> bool:
        """Check if input is a PDF file."""
        path = Path(input_str)
        return path.exists() and path.suffix.lower() == ".pdf"

    def ingest(self, input_str: str | Path) -> list[Source]:
        """Extract text from PDF file.

        Requires: pip install pypdf
        """
        path = Path(input_str)
        if not path.exists():
            return []

        try:
            try:
                from pypdf import PdfReader
            except ImportError:
                return []

            reader = PdfReader(path)
            text_parts = []

            for page in reader.pages:
                text_parts.append(page.extract_text())

            text = "\n".join(text_parts)

            # Extract title from filename or PDF metadata
            title = path.stem
            metadata = {
                "title": title,
                "file": str(path),
                "platform": "pdf",
                "pages": len(reader.pages),
            }

            # Add PDF metadata if available
            if reader.metadata:
                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title
                if reader.metadata.author:
                    metadata["author"] = reader.metadata.author
                if reader.metadata.subject:
                    metadata["subject"] = reader.metadata.subject

            return [
                Source(
                    source_id=path.stem,
                    source_type="book",
                    text=text,
                    metadata=metadata,
                    raw_format="pdf",
                )
            ]
        except Exception as e:
            return []


class TextIngester(Ingester):
    """Fallback: ingest plain text."""

    def can_ingest(self, input_str: str | Path) -> bool:
        """Always return True (fallback)."""
        return True

    def ingest(self, input_str: str | Path) -> list[Source]:
        """Handle raw text or unknown input."""
        path = Path(input_str)
        # Try to read as file first
        if path.exists():
            try:
                text = path.read_text(encoding="utf-8")
                return [
                    Source(
                        source_id=path.stem,
                        source_type="unknown",
                        text=text,
                        metadata={"file": str(path)},
                        raw_format="text",
                    )
                ]
            except Exception:
                pass

        # Fallback: treat as raw text
        text = str(input_str)
        return [
            Source(
                source_id="raw-text",
                source_type="unknown",
                text=text,
                metadata={},
                raw_format="text",
            )
        ]


def ingest_auto(input_str: str | Path) -> list[Source]:
    """Auto-detect format and ingest.

    Tries ingesters in order:
    1. YouTube
    2. Substack
    3. Twitter
    4. Markdown file
    5. PDF file
    6. Text file (fallback)

    Args:
        input_str: URL, file path, or raw text

    Returns:
        List of Source objects

    Raises:
        ValueError: If input cannot be ingested
    """
    ingesters = [
        YouTubeIngester(),
        SubstackIngester(),
        TwitterIngester(),
        MarkdownIngester(),
        PDFIngester(),
        TextIngester(),
    ]

    for ingester in ingesters:
        if ingester.can_ingest(input_str):
            sources = ingester.ingest(input_str)
            if sources:
                return sources

    return []


def ingest_batch(
    inputs: list[str | Path], output_dir: Optional[Path] = None
) -> dict[str, Source]:
    """Ingest multiple sources at once.

    Args:
        inputs: List of URLs, file paths, or raw text
        output_dir: Optional directory to save ingested sources as JSON

    Returns:
        Dictionary mapping source_id to Source objects
    """
    sources = {}

    for input_item in inputs:
        ingested = ingest_auto(input_item)
        for source in ingested:
            sources[source.source_id] = source

    # Save to directory if specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for source_id, source in sources.items():
            output_file = output_dir / f"{source_id}.json"
            output_file.write_text(source.model_dump_json(indent=2))

    return sources
