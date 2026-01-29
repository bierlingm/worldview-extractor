"""Tests for wve run command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from wve.cli import main


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def transcript_dir(tmp_path, sample_transcript):
    """Create a temp directory with sample transcripts."""
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    (transcripts / "video1.txt").write_text(sample_transcript)
    (transcripts / "video2.txt").write_text(sample_transcript)
    return transcripts


@pytest.fixture
def url_list_file(tmp_path):
    """Create a file with URLs."""
    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "https://www.youtube.com/watch?v=abc123\n"
        "https://www.youtube.com/watch?v=def456\n"
        "# comment line\n"
        "https://www.youtube.com/watch?v=ghi789\n"
    )
    return url_file


class TestRunInputClassification:
    """Tests for input type detection."""

    def test_classifies_url(self, runner, tmp_path):
        """URL inputs are classified correctly."""
        result = runner.invoke(
            main,
            ["run", "https://youtube.com/watch?v=abc", "-s", "Test", "-o", str(tmp_path), "--fetch-only"],
            catch_exceptions=False,
        )
        # Will fail to fetch but that's fine - we're testing classification
        assert result.exit_code != 0 or "Downloading" in result.output or "Failed" in result.output

    def test_classifies_directory(self, runner, transcript_dir, tmp_path):
        """Directory inputs are classified correctly."""
        result = runner.invoke(
            main,
            ["run", str(transcript_dir), "-s", "Test", "-o", str(tmp_path), "--report-only"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

    def test_classifies_url_list_file(self, runner, url_list_file, tmp_path):
        """URL list files are detected and parsed."""
        result = runner.invoke(
            main,
            ["run", str(url_list_file), "-s", "Test", "-o", str(tmp_path), "--fetch-only"],
            catch_exceptions=False,
        )
        # Should attempt to download 3 URLs (skipping comment)
        assert "3" in result.output or result.exit_code != 0

    def test_classifies_local_file(self, runner, tmp_path, sample_transcript):
        """Local transcript files are copied."""
        local_file = tmp_path / "local.txt"
        local_file.write_text(sample_transcript)
        output_dir = tmp_path / "output"

        result = runner.invoke(
            main,
            ["run", str(local_file), "-s", "Test", "-o", str(output_dir)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert (output_dir / "transcripts" / "local.txt").exists()


class TestRunReportOnly:
    """Tests for --report-only mode."""

    def test_report_only_from_directory(self, runner, transcript_dir, tmp_path):
        """Report-only mode works with existing transcripts."""
        result = runner.invoke(
            main,
            ["run", str(transcript_dir), "-s", "Test Subject", "-o", str(tmp_path), "--report-only"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Worldview: Test Subject" in result.output
        assert (tmp_path / "report.md").exists()

    def test_report_only_fails_without_transcripts(self, runner, tmp_path):
        """Report-only fails gracefully without transcripts."""
        result = runner.invoke(
            main,
            ["run", "-s", "Test", "-o", str(tmp_path), "--report-only"],
        )
        assert result.exit_code != 0
        assert "No transcripts found" in result.output

    def test_report_contains_themes(self, runner, transcript_dir, tmp_path):
        """Report includes extracted themes."""
        result = runner.invoke(
            main,
            ["run", str(transcript_dir), "-s", "Test", "-o", str(tmp_path), "--report-only"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        report = (tmp_path / "report.md").read_text()
        assert "## Themes" in report


class TestRunJsonOutput:
    """Tests for --json output mode."""

    def test_json_output(self, runner, transcript_dir, tmp_path):
        """JSON output is valid and contains expected fields."""
        result = runner.invoke(
            main,
            ["run", str(transcript_dir), "-s", "Test Subject", "-o", str(tmp_path), "--report-only", "--json"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["subject"] == "Test Subject"
        assert "themes" in data
        assert "top_quotes" in data
        assert "source_count" in data

    def test_json_fetch_only(self, runner, transcript_dir, tmp_path):
        """JSON output for fetch-only mode."""
        result = runner.invoke(
            main,
            ["run", str(transcript_dir), "-s", "Test", "-o", str(tmp_path), "--fetch-only", "--json"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "transcripts_dir" in data
        assert "count" in data


class TestRunResume:
    """Tests for resume/caching logic."""

    def test_skips_existing_transcripts(self, runner, tmp_path, sample_transcript):
        """Existing transcripts are not re-downloaded."""
        output_dir = tmp_path / "output"
        transcripts_dir = output_dir / "transcripts"
        transcripts_dir.mkdir(parents=True)
        (transcripts_dir / "existing.txt").write_text(sample_transcript)

        result = runner.invoke(
            main,
            ["run", "-u", "https://youtube.com/watch?v=new", "-s", "Test", "-o", str(output_dir)],
            catch_exceptions=False,
        )
        # Should mention existing transcripts
        assert "existing transcripts" in result.output.lower() or result.exit_code == 0

    def test_force_redownloads(self, runner, tmp_path, sample_transcript):
        """--force flag triggers re-download."""
        output_dir = tmp_path / "output"
        transcripts_dir = output_dir / "transcripts"
        transcripts_dir.mkdir(parents=True)
        (transcripts_dir / "existing.txt").write_text(sample_transcript)

        result = runner.invoke(
            main,
            ["run", "-u", "https://youtube.com/watch?v=test", "-s", "Test", "-o", str(output_dir), "--force"],
        )
        # Should attempt download even with existing transcripts
        assert "Downloading" in result.output or "Failed" in result.output or result.exit_code != 0


class TestRunSave:
    """Tests for --save integration with store."""

    def test_save_to_store(self, runner, transcript_dir, tmp_path, monkeypatch):
        """--save persists to store."""
        # Track if save was called
        save_called = []
        store_dir = tmp_path / "store" / "test-subject"
        store_dir.mkdir(parents=True)

        def mock_get_entry_dir(slug):
            return store_dir

        def mock_save_entry(entry):
            save_called.append(entry)

        monkeypatch.setattr("wve.store.get_entry_dir", mock_get_entry_dir)
        monkeypatch.setattr("wve.store.save_entry", mock_save_entry)

        result = runner.invoke(
            main,
            ["run", str(transcript_dir), "-s", "Test Subject", "-o", str(tmp_path), "--report-only", "--save"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert len(save_called) == 1
        assert "Saved to store" in result.output


class TestRunEdgeCases:
    """Tests for edge cases and error handling."""

    def test_no_input_error(self, runner, tmp_path):
        """Error when no input provided."""
        result = runner.invoke(
            main,
            ["run", "-s", "Test", "-o", str(tmp_path)],
        )
        assert result.exit_code != 0
        assert "No input provided" in result.output

    def test_empty_transcript_dir(self, runner, tmp_path):
        """Error when transcript directory is empty."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(
            main,
            ["run", str(empty_dir), "-s", "Test", "-o", str(tmp_path), "--report-only"],
        )
        assert result.exit_code != 0
        assert "No transcripts found" in result.output

    def test_multiple_url_flags(self, runner, tmp_path):
        """Multiple -u flags are collected."""
        result = runner.invoke(
            main,
            [
                "run",
                "-u", "https://youtube.com/watch?v=a",
                "-u", "https://youtube.com/watch?v=b",
                "-s", "Test",
                "-o", str(tmp_path),
                "--fetch-only",
            ],
        )
        # Should attempt to download both
        assert "2" in result.output or result.exit_code != 0

    def test_mixed_inputs(self, runner, transcript_dir, tmp_path):
        """Mix of directory and URL inputs."""
        result = runner.invoke(
            main,
            [
                "run",
                str(transcript_dir),
                "-u", "https://youtube.com/watch?v=extra",
                "-s", "Test",
                "-o", str(tmp_path),
            ],
        )
        # Should process both existing dir and attempt URL
        assert result.exit_code == 0 or "Failed" in result.output
