"""Tests for classification heuristics (v0.2)."""

import json
from datetime import datetime

import pytest
from click.testing import CliRunner

from wve.classify import (
    CandidateSet,
    VideoCandidate,
    classify_candidate,
    classify_candidates,
    update_identity_from_feedback,
)
from wve.cli import main
from wve.identity import Channel, Identity


@pytest.fixture
def sample_candidate():
    """A sample video candidate."""
    return VideoCandidate(
        id="abc123",
        title="Interview with Skinner Layne on Entrepreneurship",
        channel="TechTalks",
        channel_id="UC_techtalks",
        duration_seconds=1800,
        url="https://youtube.com/watch?v=abc123",
        published=datetime(2024, 1, 15),
    )


@pytest.fixture
def sample_identity():
    """A sample identity for testing."""
    return Identity(
        slug="skinner-layne",
        display_name="Skinner Layne",
        channels=[
            Channel(platform="youtube", id="exikiex", url="https://youtube.com/@exikiex")
        ],
        confirmed_videos=["confirmed1", "confirmed2"],
        rejected_videos=["rejected1"],
        trusted_channels=["UC_trusted"],
        suspicious_patterns=["cover", "reaction"],
    )


class TestVideoCandidateModel:
    def test_create(self, sample_candidate):
        assert sample_candidate.id == "abc123"
        assert sample_candidate.classification is None

    def test_classification_fields(self):
        c = VideoCandidate(
            id="test",
            title="Test",
            channel="Chan",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
            classification="likely",
            classification_reason="test reason",
            confidence=0.9,
        )
        assert c.classification == "likely"
        assert c.confidence == 0.9


class TestCandidateSetModel:
    def test_create(self, sample_candidate):
        cs = CandidateSet(
            query="Skinner Layne",
            identity_slug="skinner-layne",
            candidates=[sample_candidate],
        )
        assert cs.query == "Skinner Layne"
        assert len(cs.candidates) == 1


class TestClassifyCandidate:
    def test_full_name_in_title(self):
        c = VideoCandidate(
            id="test",
            title="Skinner Layne on Education",
            channel="Podcast",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(c, "Skinner Layne")
        assert classification == "likely"
        assert "full name in title" in reason
        assert confidence >= 0.8

    def test_all_parts_in_title(self):
        c = VideoCandidate(
            id="test",
            title="Interview with Layne, Skinner - Tech Talk",
            channel="Podcast",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(c, "Skinner Layne")
        assert classification == "likely"
        assert "all name parts" in reason

    def test_partial_match_uncertain(self):
        c = VideoCandidate(
            id="test",
            title="The Layne Brothers Podcast",
            channel="Music",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(c, "Skinner Layne")
        assert classification == "uncertain"
        assert "partial" in reason

    def test_entertainment_false_positive(self):
        c = VideoCandidate(
            id="test",
            title="Layne Staley Cover - Best Tribute",
            channel="MusicCovers",
            channel_id="UC123",
            duration_seconds=300,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(c, "Skinner Layne")
        assert classification == "false_positive"
        assert "entertainment" in reason or "cover" in reason.lower()

    def test_no_match(self):
        c = VideoCandidate(
            id="test",
            title="Completely unrelated video about cooking",
            channel="FoodNetwork",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(c, "Skinner Layne")
        assert classification == "false_positive"
        assert "no name match" in reason

    def test_interview_format_with_partial(self):
        c = VideoCandidate(
            id="test",
            title="Podcast Episode #45: Layne discusses startups",
            channel="StartupPod",
            channel_id="UC123",
            duration_seconds=3600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(c, "Skinner Layne")
        assert classification == "uncertain"
        assert "interview" in reason or "partial" in reason


class TestClassifyWithIdentity:
    def test_from_subjects_channel(self, sample_identity):
        c = VideoCandidate(
            id="test",
            title="Random video title",
            channel="exikiex",
            channel_id="exikiex",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(
            c, "Skinner Layne", sample_identity
        )
        assert classification == "likely"
        assert "own channel" in reason
        assert confidence >= 0.95

    def test_from_trusted_channel(self, sample_identity):
        c = VideoCandidate(
            id="test",
            title="Random title",
            channel="Trusted Show",
            channel_id="UC_trusted",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(
            c, "Skinner Layne", sample_identity
        )
        assert classification == "likely"
        assert "trusted channel" in reason

    def test_previously_confirmed(self, sample_identity):
        c = VideoCandidate(
            id="confirmed1",
            title="Whatever",
            channel="Any",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(
            c, "Skinner Layne", sample_identity
        )
        assert classification == "likely"
        assert "previously confirmed" in reason
        assert confidence == 1.0

    def test_previously_rejected(self, sample_identity):
        c = VideoCandidate(
            id="rejected1",
            title="Whatever",
            channel="Any",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(
            c, "Skinner Layne", sample_identity
        )
        assert classification == "false_positive"
        assert "previously rejected" in reason

    def test_suspicious_pattern(self, sample_identity):
        c = VideoCandidate(
            id="test",
            title="Skinner Layne Song Cover",
            channel="Music",
            channel_id="UC123",
            duration_seconds=300,
            url="https://example.com",
            published=datetime.now(),
        )
        classification, reason, confidence = classify_candidate(
            c, "Skinner Layne", sample_identity
        )
        assert classification == "false_positive"
        assert "suspicious pattern" in reason or "cover" in reason.lower()


class TestClassifyCandidates:
    def test_bulk_classify(self):
        candidates = [
            VideoCandidate(
                id="1",
                title="Skinner Layne Interview",
                channel="Pod",
                channel_id="UC1",
                duration_seconds=600,
                url="https://example.com/1",
                published=datetime.now(),
            ),
            VideoCandidate(
                id="2",
                title="Unrelated Video",
                channel="Other",
                channel_id="UC2",
                duration_seconds=600,
                url="https://example.com/2",
                published=datetime.now(),
            ),
        ]

        classify_candidates(candidates, "Skinner Layne")

        assert candidates[0].classification == "likely"
        assert candidates[1].classification == "false_positive"


class TestUpdateIdentityFromFeedback:
    def test_confirm_adds_to_confirmed(self, sample_identity):
        c = VideoCandidate(
            id="new_video",
            title="Test",
            channel="Chan",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        update_identity_from_feedback(sample_identity, c, confirmed=True)
        assert "new_video" in sample_identity.confirmed_videos

    def test_reject_adds_to_rejected(self, sample_identity):
        c = VideoCandidate(
            id="new_video",
            title="Test",
            channel="Chan",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        update_identity_from_feedback(sample_identity, c, confirmed=False)
        assert "new_video" in sample_identity.rejected_videos

    def test_confirm_removes_from_rejected(self, sample_identity):
        c = VideoCandidate(
            id="rejected1",
            title="Test",
            channel="Chan",
            channel_id="UC123",
            duration_seconds=600,
            url="https://example.com",
            published=datetime.now(),
        )
        assert "rejected1" in sample_identity.rejected_videos
        update_identity_from_feedback(sample_identity, c, confirmed=True)
        assert "rejected1" not in sample_identity.rejected_videos
        assert "rejected1" in sample_identity.confirmed_videos


class TestDiscoverCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_search(self, mocker):
        """Mock search_videos to avoid network calls."""
        from wve.models import SearchResult, VideoMetadata

        mock = mocker.patch("wve.search.search_videos")
        mock.return_value = SearchResult(
            query="Test Person",
            max_results=10,
            videos=[
                VideoMetadata(
                    id="vid1",
                    title="Interview with Test Person",
                    channel="Podcast Channel",
                    channel_id="UC_podcast",
                    duration_seconds=1800,
                    url="https://youtube.com/watch?v=vid1",
                    published=datetime(2024, 1, 1),
                ),
                VideoMetadata(
                    id="vid2",
                    title="Test Song Cover",
                    channel="Music Channel",
                    channel_id="UC_music",
                    duration_seconds=300,
                    url="https://youtube.com/watch?v=vid2",
                    published=datetime(2024, 1, 2),
                ),
                VideoMetadata(
                    id="vid3",
                    title="Unrelated video",
                    channel="Random",
                    channel_id="UC_random",
                    duration_seconds=600,
                    url="https://youtube.com/watch?v=vid3",
                    published=datetime(2024, 1, 3),
                ),
            ],
        )
        return mock

    def test_discover_json(self, runner, mock_search):
        result = runner.invoke(main, ["discover", "Test Person", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["query"] == "Test Person"
        assert len(data["candidates"]) == 3

    def test_discover_classifies(self, runner, mock_search):
        result = runner.invoke(main, ["discover", "Test Person", "--json"])
        data = json.loads(result.output)

        # Find classifications
        classifications = {c["id"]: c["classification"] for c in data["candidates"]}
        assert classifications["vid1"] == "likely"  # Name in title
        assert classifications["vid2"] == "false_positive"  # Cover
        assert classifications["vid3"] == "false_positive"  # No match

    def test_discover_with_output(self, runner, mock_search, tmp_path):
        output_file = tmp_path / "candidates.json"
        result = runner.invoke(
            main, ["discover", "Test Person", "-o", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()

        data = json.loads(output_file.read_text())
        assert data["query"] == "Test Person"

    def test_discover_strict(self, runner, mock_search):
        result = runner.invoke(main, ["discover", "Test Person", "--strict", "--json"])
        data = json.loads(result.output)
        # Only vid1 has "Test Person" in title
        assert len(data["candidates"]) == 1
        assert data["candidates"][0]["id"] == "vid1"


class TestConfirmCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def candidates_file(self, tmp_path):
        """Create a candidates.json file for testing."""
        from wve.classify import CandidateSet, VideoCandidate

        candidates = CandidateSet(
            query="Test Person",
            candidates=[
                VideoCandidate(
                    id="vid1",
                    title="Interview with Test Person",
                    channel="Podcast",
                    channel_id="UC1",
                    duration_seconds=1800,
                    url="https://youtube.com/watch?v=vid1",
                    published=datetime(2024, 1, 1),
                    classification="likely",
                    classification_reason="full name in title",
                    confidence=0.85,
                ),
                VideoCandidate(
                    id="vid2",
                    title="Test Song Cover",
                    channel="Music",
                    channel_id="UC2",
                    duration_seconds=300,
                    url="https://youtube.com/watch?v=vid2",
                    published=datetime(2024, 1, 2),
                    classification="false_positive",
                    classification_reason="entertainment content",
                    confidence=0.8,
                ),
                VideoCandidate(
                    id="vid3",
                    title="Maybe Test Person",
                    channel="Unknown",
                    channel_id="UC3",
                    duration_seconds=600,
                    url="https://youtube.com/watch?v=vid3",
                    published=datetime(2024, 1, 3),
                    classification="uncertain",
                    classification_reason="partial match",
                    confidence=0.5,
                ),
            ],
        )
        path = tmp_path / "candidates.json"
        path.write_text(candidates.model_dump_json(indent=2))
        return path

    def test_confirm_batch_accept(self, runner, candidates_file):
        result = runner.invoke(
            main, ["confirm", str(candidates_file), "--accept", "1,3", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["count"]["confirmed"] == 2
        assert data["count"]["rejected"] == 0

    def test_confirm_batch_reject(self, runner, candidates_file):
        result = runner.invoke(
            main, ["confirm", str(candidates_file), "--reject", "2", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["count"]["rejected"] == 1

    def test_confirm_accept_likely(self, runner, candidates_file):
        result = runner.invoke(
            main, ["confirm", str(candidates_file), "--accept-likely", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Only vid1 is "likely"
        assert data["count"]["confirmed"] == 1
        assert data["confirmed"][0]["id"] == "vid1"

    def test_confirm_with_output(self, runner, candidates_file, tmp_path):
        output_file = tmp_path / "confirmed.json"
        result = runner.invoke(
            main,
            ["confirm", str(candidates_file), "--accept", "1", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()

        data = json.loads(output_file.read_text())
        assert len(data["candidates"]) == 1
        assert data["candidates"][0]["id"] == "vid1"

    def test_confirm_range(self, runner, candidates_file):
        result = runner.invoke(
            main, ["confirm", str(candidates_file), "--accept", "1-3", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["count"]["confirmed"] == 3

    def test_confirm_updates_identity(self, runner, candidates_file, tmp_path, monkeypatch):
        """Test that confirmations update the identity."""
        from wve.identity import create_identity, load_identity

        # Use temp identity dir
        identity_dir = tmp_path / "identities"
        identity_dir.mkdir()
        monkeypatch.setattr("wve.identity.DEFAULT_IDENTITY_DIR", identity_dir)

        create_identity("Test Person", slug="test-person")

        result = runner.invoke(
            main,
            [
                "confirm",
                str(candidates_file),
                "--identity", "test-person",
                "--accept", "1",
                "--reject", "2",
                "--json",
            ],
        )
        assert result.exit_code == 0

        identity = load_identity("test-person")
        assert "vid1" in identity.confirmed_videos
        assert "vid2" in identity.rejected_videos


class TestFetchCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def confirmed_file(self, tmp_path):
        """Create a confirmed.json file for testing."""
        from wve.classify import CandidateSet, VideoCandidate

        candidates = CandidateSet(
            query="Test Person",
            candidates=[
                VideoCandidate(
                    id="vid1",
                    title="Interview with Test Person",
                    channel="Podcast",
                    channel_id="UC1",
                    duration_seconds=1800,
                    url="https://youtube.com/watch?v=vid1",
                    published=datetime(2024, 1, 1),
                    confirmed=True,
                ),
                VideoCandidate(
                    id="vid2",
                    title="Another Video",
                    channel="Channel",
                    channel_id="UC2",
                    duration_seconds=600,
                    url="https://youtube.com/watch?v=vid2",
                    published=datetime(2024, 1, 2),
                    confirmed=True,
                ),
            ],
        )
        path = tmp_path / "confirmed.json"
        path.write_text(candidates.model_dump_json(indent=2))
        return path

    @pytest.fixture
    def mock_download(self, mocker, tmp_path):
        """Mock download_transcript to avoid network calls."""
        def fake_download(url, output_dir, lang="en"):
            # Extract video ID
            import re
            match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
            vid_id = match.group(1) if match else "unknown"
            path = output_dir / f"{vid_id}.txt"
            path.write_text(f"Transcript for {vid_id}")
            return path

        mock = mocker.patch("wve.transcripts.download_transcript", side_effect=fake_download)
        return mock

    def test_fetch_from_file(self, runner, confirmed_file, mock_download, tmp_path):
        output_dir = tmp_path / "transcripts"
        result = runner.invoke(
            main, ["fetch", str(confirmed_file), "-o", str(output_dir), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["fetched"] == 2
        assert len(data["transcripts"]) == 2

    def test_fetch_from_identity(self, runner, mock_download, tmp_path, monkeypatch):
        """Test fetching from identity's confirmed videos."""
        from wve.identity import create_identity, add_video_to_identity

        identity_dir = tmp_path / "identities"
        identity_dir.mkdir()
        monkeypatch.setattr("wve.identity.DEFAULT_IDENTITY_DIR", identity_dir)

        create_identity("Test Person", slug="test-person")
        add_video_to_identity("test-person", "vid1", confirmed=True)
        add_video_to_identity("test-person", "vid2", confirmed=True)

        output_dir = tmp_path / "transcripts"
        result = runner.invoke(
            main, ["fetch", "--identity", "test-person", "-o", str(output_dir), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["fetched"] == 2

    def test_fetch_no_input(self, runner):
        result = runner.invoke(main, ["fetch", "--json"])
        assert result.exit_code == 1


class TestFromUrlsCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_download(self, mocker, tmp_path):
        """Mock download_transcript to avoid network calls."""
        def fake_download(url, output_dir, lang="en"):
            import re
            match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
            vid_id = match.group(1) if match else "unknown"
            path = output_dir / f"{vid_id}.txt"
            path.write_text(f"Transcript for {vid_id}")
            return path

        mock = mocker.patch("wve.transcripts.download_transcript", side_effect=fake_download)
        return mock

    def test_from_urls_file(self, runner, mock_download, tmp_path):
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://youtube.com/watch?v=abc123\nhttps://youtube.com/watch?v=def456")
        
        output_dir = tmp_path / "transcripts"
        result = runner.invoke(
            main, ["from-urls", str(urls_file), "-o", str(output_dir), "-y", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["fetched"] == 2

    def test_from_urls_inline(self, runner, mock_download, tmp_path):
        output_dir = tmp_path / "transcripts"
        result = runner.invoke(
            main, [
                "from-urls",
                "-u", "https://youtube.com/watch?v=abc123",
                "-u", "https://youtube.com/watch?v=def456",
                "-o", str(output_dir),
                "-y",
                "--json"
            ]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["fetched"] == 2

    def test_from_urls_no_input(self, runner):
        result = runner.invoke(main, ["from-urls", "--json"])
        assert result.exit_code == 1
