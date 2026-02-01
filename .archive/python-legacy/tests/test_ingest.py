"""Tests for input ingestion layer (Task #2)."""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from wve.ingest import (
    Ingester,
    MarkdownIngester,
    PDFIngester,
    Source,
    SubstackIngester,
    TextIngester,
    TwitterIngester,
    YouTubeIngester,
    ingest_auto,
    ingest_batch,
)


class TestSource:
    """Test Source model."""

    def test_create_source(self):
        """Create a Source object."""
        source = Source(
            source_id="test-1",
            source_type="article",
            text="Test content",
            raw_format="markdown",
            metadata={"title": "Test Article"},
        )
        assert source.source_id == "test-1"
        assert source.source_type == "article"
        assert len(source.text) > 0
        assert source.metadata["title"] == "Test Article"

    def test_source_hashable(self):
        """Source objects should be hashable."""
        source1 = Source(
            source_id="test-1",
            source_type="article",
            text="Content 1",
            raw_format="text",
        )
        source2 = Source(
            source_id="test-2",
            source_type="article",
            text="Content 2",
            raw_format="text",
        )
        # Should be able to add to set
        source_set = {source1, source2}
        assert len(source_set) == 2


class TestYouTubeIngester:
    """Test YouTube ingestion."""

    def test_can_ingest_youtube_url(self):
        """Recognize YouTube URLs."""
        ingester = YouTubeIngester()
        assert ingester.can_ingest("https://youtube.com/watch?v=dQw4w9WgXcQ")
        assert ingester.can_ingest("https://youtu.be/dQw4w9WgXcQ")
        assert ingester.can_ingest("https://youtube-nocookie.com/embed/dQw4w9WgXcQ")

    def test_cannot_ingest_non_youtube(self):
        """Reject non-YouTube inputs."""
        ingester = YouTubeIngester()
        assert not ingester.can_ingest("/path/to/file.md")
        assert not ingester.can_ingest("https://example.com")

    def test_ingest_returns_empty_for_invalid_video(self):
        """Return empty list for invalid video IDs."""
        ingester = YouTubeIngester()
        # Invalid URL should return empty list
        results = ingester.ingest("https://youtube.com/watch?v=invalid")
        assert results == []


class TestMarkdownIngester:
    """Test Markdown file ingestion."""

    def test_can_ingest_markdown_files(self):
        """Recognize markdown files."""
        ingester = MarkdownIngester()
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("# Test")
            assert ingester.can_ingest(md_file)

    def test_cannot_ingest_non_markdown(self):
        """Reject non-markdown inputs."""
        ingester = MarkdownIngester()
        assert not ingester.can_ingest("https://example.com")
        assert not ingester.can_ingest("string content")

    def test_ingest_markdown_file(self):
        """Ingest markdown file content."""
        ingester = MarkdownIngester()
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "blog.md"
            content = dedent("""
                # My Article Title

                This is the body of the article.
                It has multiple paragraphs.
                """).strip()
            md_file.write_text(content)

            results = ingester.ingest(md_file)

            assert len(results) == 1
            source = results[0]
            assert source.source_id == "blog"
            assert source.source_type == "article"
            assert source.raw_format == "markdown"
            assert "My Article Title" in source.text
            assert source.metadata["title"] == "My Article Title"

    def test_ingest_markdown_without_frontmatter(self):
        """Ingest markdown without YAML frontmatter."""
        ingester = MarkdownIngester()
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "simple.md"
            md_file.write_text("# Simple Title\n\nContent here.")

            results = ingester.ingest(md_file)
            assert len(results) == 1
            assert "Simple Title" in results[0].text


class TestTextIngester:
    """Test plain text ingestion (fallback)."""

    def test_can_ingest_anything(self):
        """Text ingester can handle anything (fallback)."""
        ingester = TextIngester()
        assert ingester.can_ingest("https://example.com")
        assert ingester.can_ingest("/any/path.txt")
        assert ingester.can_ingest("raw text content")

    def test_ingest_raw_text(self):
        """Ingest raw text string."""
        ingester = TextIngester()
        text = "This is raw text content for testing."

        results = ingester.ingest(text)

        assert len(results) == 1
        source = results[0]
        assert source.source_id == "raw-text"
        assert source.source_type == "unknown"
        assert source.text == text

    def test_ingest_text_file(self):
        """Ingest plain text file."""
        ingester = TextIngester()
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "notes.txt"
            txt_file.write_text("Some notes here.")

            results = ingester.ingest(txt_file)

            assert len(results) == 1
            assert results[0].text == "Some notes here."


class TestIngestAuto:
    """Test automatic format detection."""

    def test_auto_detects_markdown(self):
        """Auto-detect markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("# Title\n\nContent")

            results = ingest_auto(md_file)

            assert len(results) == 1
            assert results[0].raw_format == "markdown"

    def test_auto_detects_youtube_url(self):
        """Auto-detect YouTube URLs (falls back to text if invalid)."""
        # Will return raw text because the ID is invalid
        # YouTubeIngester returns empty, so falls back to TextIngester
        results = ingest_auto("https://youtube.com/watch?v=invalid")
        assert len(results) == 1
        # Falls back to text ingester
        assert results[0].raw_format == "text"

    def test_auto_detects_raw_text(self):
        """Fall back to text ingester for unknown input."""
        results = ingest_auto("Some arbitrary text content here")

        assert len(results) == 1
        assert results[0].source_type == "unknown"
        assert results[0].raw_format == "text"


class TestIngestBatch:
    """Test batch ingestion."""

    def test_batch_ingest_multiple_sources(self):
        """Ingest multiple sources at once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create markdown files
            (Path(tmpdir) / "file1.md").write_text("# File 1\n\nContent 1")
            (Path(tmpdir) / "file2.md").write_text("# File 2\n\nContent 2")

            inputs = [Path(tmpdir) / "file1.md", Path(tmpdir) / "file2.md"]
            sources = ingest_batch(inputs)

            assert len(sources) == 2
            assert "file1" in sources
            assert "file2" in sources

    def test_batch_ingest_saves_to_directory(self):
        """Save ingested sources to output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test\n\nContent")

            # Ingest to output directory
            output_dir = Path(tmpdir) / "output"
            sources = ingest_batch([input_file], output_dir)

            # Check output directory
            assert output_dir.exists()
            assert (output_dir / "test.json").exists()

            # Check saved content
            import json

            with open(output_dir / "test.json") as f:
                saved = json.load(f)
            assert saved["source_id"] == "test"
            assert saved["raw_format"] == "markdown"


class TestIngesterInterface:
    """Test ingester ABC interface."""

    def test_ingester_subclass_implements_methods(self):
        """Subclasses must implement abstract methods."""
        # Create a minimal concrete implementation
        class MinimalIngester(Ingester):
            def can_ingest(self, input_str):
                return False

            def ingest(self, input_str):
                return []

        ingester = MinimalIngester()
        assert not ingester.can_ingest("anything")
        assert ingester.ingest("anything") == []


class TestSubstackIngester:
    """Test Substack ingestion (basic)."""

    def test_can_ingest_substack_url(self):
        """Recognize Substack URLs."""
        ingester = SubstackIngester()
        assert ingester.can_ingest("https://example.substack.com/p/article-slug")

    def test_cannot_ingest_non_substack(self):
        """Reject non-Substack inputs."""
        ingester = SubstackIngester()
        assert not ingester.can_ingest("https://example.com")


class TestTwitterIngester:
    """Test Twitter/X ingestion (basic)."""

    def test_can_ingest_twitter_url(self):
        """Recognize Twitter URLs."""
        ingester = TwitterIngester()
        assert ingester.can_ingest("https://twitter.com/user/status/123")
        assert ingester.can_ingest("https://x.com/user/status/123")

    def test_cannot_ingest_non_twitter(self):
        """Reject non-Twitter inputs."""
        ingester = TwitterIngester()
        assert not ingester.can_ingest("https://example.com")


class TestPDFIngester:
    """Test PDF ingestion (basic)."""

    def test_can_ingest_pdf_files(self):
        """Recognize PDF files."""
        ingester = PDFIngester()
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_file = Path(tmpdir) / "document.pdf"
            pdf_file.write_text("%PDF-1.4\nFake PDF content")
            assert ingester.can_ingest(pdf_file)

    def test_cannot_ingest_non_pdf(self):
        """Reject non-PDF inputs."""
        ingester = PDFIngester()
        assert not ingester.can_ingest("https://example.com")
        assert not ingester.can_ingest("document.txt")
