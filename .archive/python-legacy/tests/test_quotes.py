"""Tests for quote extraction (v0.2)."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from wve.cli import main
from wve.quotes import (
    Quote,
    QuoteCollection,
    extract_quotes,
    extract_quotes_from_dir,
    score_sentence,
    split_sentences,
)


class TestSplitSentences:
    def test_basic(self):
        text = "Hello world. This is a test. Another one."
        sentences = split_sentences(text)
        assert len(sentences) == 3

    def test_handles_newlines(self):
        text = "Hello\n\nworld.  This is\na test."
        sentences = split_sentences(text)
        assert "Hello world" in sentences[0]


class TestScoreSentence:
    def test_opinion_starter(self):
        score, reasons, _ = score_sentence("I believe that education is broken.")
        assert score >= 0.3
        assert any("opinion_starter" in r for r in reasons)

    def test_contrarian(self):
        score, reasons, is_contrarian = score_sentence(
            "Most people think success comes from talent, but actually it's about persistence."
        )
        assert is_contrarian
        assert "contrarian" in reasons

    def test_specific_numbers(self):
        score, reasons, _ = score_sentence("We grew 50% year over year for 3 years.")
        assert "specific" in reasons

    def test_low_score_generic(self):
        score, _, _ = score_sentence("It was nice.")
        assert score < 0.3


class TestExtractQuotes:
    def test_basic(self):
        text = """
        I believe that education is fundamentally broken in America.
        The weather is nice today.
        Most people think entrepreneurship is about ideas, but actually it's about execution.
        """
        quotes = extract_quotes(text, "test", "Test Source")
        assert len(quotes) >= 1
        # Should find the opinion/contrarian statements
        texts = [q.text for q in quotes]
        assert any("believe" in t.lower() or "most people" in t.lower() for t in texts)

    def test_filters_short(self):
        text = "Short. Very short. Too short."
        quotes = extract_quotes(text, "test", "Test", min_words=5)
        assert len(quotes) == 0


class TestQuoteCollection:
    def test_model(self):
        collection = QuoteCollection(
            subject="Test Person",
            quotes=[
                Quote(text="Test quote", source_id="src1", source_title="Source 1"),
            ],
            source_count=1,
        )
        assert collection.subject == "Test Person"
        assert len(collection.quotes) == 1


class TestExtractQuotesFromDir:
    @pytest.fixture
    def transcript_dir(self, tmp_path):
        """Create a directory with sample transcripts."""
        (tmp_path / "video1.txt").write_text(
            "I believe that learning should be self-directed. "
            "Most people think school prepares you for life, but actually it teaches conformity. "
            "The weather is nice."
        )
        (tmp_path / "video2.txt").write_text(
            "I think the future belongs to those who can learn independently. "
            "Traditional education has failed us completely."
        )
        return tmp_path

    def test_extract_from_dir(self, transcript_dir):
        collection = extract_quotes_from_dir(transcript_dir)
        assert collection.source_count == 2
        assert len(collection.quotes) >= 2


class TestQuotesCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def transcript_dir(self, tmp_path):
        """Create a directory with sample transcripts."""
        (tmp_path / "video1.txt").write_text(
            "I believe that learning should be self-directed and autonomous. "
            "Most people think school prepares you for life, but actually it teaches conformity and obedience. "
        )
        return tmp_path

    def test_quotes_json(self, runner, transcript_dir):
        result = runner.invoke(main, ["quotes", str(transcript_dir), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "quotes" in data
        assert data["source_count"] == 1

    def test_quotes_with_output(self, runner, transcript_dir, tmp_path):
        output = tmp_path / "quotes.json"
        result = runner.invoke(main, ["quotes", str(transcript_dir), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()


class TestThemesCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def transcript_dir(self, tmp_path):
        """Create a directory with sample transcripts."""
        (tmp_path / "video1.txt").write_text(
            "I believe that education should empower students to think independently. "
            "Education is the key to solving many problems in society. "
            "Traditional education has failed to keep pace with technology."
        )
        return tmp_path

    def test_themes_json(self, runner, transcript_dir):
        result = runner.invoke(main, ["themes", str(transcript_dir), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "themes" in data


class TestContrastCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def transcript_dir(self, tmp_path):
        """Create a directory with sample transcripts."""
        (tmp_path / "video1.txt").write_text(
            "Most people think success comes from hard work, but actually it's about leverage. "
            "Contrary to popular belief, formal education is often a hindrance to success."
        )
        return tmp_path

    def test_contrast_json(self, runner, transcript_dir):
        result = runner.invoke(
            main, ["contrast", str(transcript_dir), "-s", "Test Person", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["subject"] == "Test Person"
        assert "contrarian_count" in data
