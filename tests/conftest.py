"""Pytest configuration and shared fixtures for worldview-extractor tests."""

import json
from pathlib import Path
from typing import Any
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_transcript() -> str:
    """Load sample transcript text."""
    return (FIXTURES_DIR / "sample_transcript.txt").read_text()


@pytest.fixture
def sample_transcript_noisy() -> str:
    """Load noisy sample transcript (encoding issues, repetition)."""
    return (FIXTURES_DIR / "sample_transcript_noisy.txt").read_text()


@pytest.fixture
def sample_video_metadata() -> list[dict[str, Any]]:
    """Sample video metadata from search."""
    return [
        {
            "id": "akUVyB8LLdA",
            "title": "#870- E.M. Burlingame",
            "channel": "Shaun Newman Podcast",
            "channel_id": "UC123",
            "duration_seconds": 5400,
            "url": "https://www.youtube.com/watch?v=akUVyB8LLdA",
            "published": "2025-07-02T00:00:00Z",
        },
        {
            "id": "-Ucfj5zRz7k",
            "title": "252 | EM Burlingame",
            "channel": "Citizen Podcast",
            "channel_id": "UC456",
            "duration_seconds": 4800,
            "url": "https://www.youtube.com/watch?v=-Ucfj5zRz7k",
            "published": "2025-02-02T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_extraction() -> dict[str, Any]:
    """Load sample extraction results."""
    return json.loads((FIXTURES_DIR / "sample_extraction.json").read_text())


@pytest.fixture
def sample_clusters() -> dict[str, Any]:
    """Load sample cluster results."""
    return json.loads((FIXTURES_DIR / "sample_clusters.json").read_text())


@pytest.fixture
def ground_truth_worldview() -> dict[str, Any]:
    """Ground truth worldview for quality testing."""
    return {
        "subject": "EM Burlingame",
        "expected_themes": [
            "civilizations vs nation-states",
            "praetorian/parasitic empire",
            "financialist kill-chain",
            "estrogen vs testosterone logic",
            "bioelectric/third-generation medicine",
        ],
        "expected_entities": {
            "PERSON": ["Putin", "Stalin", "Mao", "Constantine"],
            "GPE": ["China", "Russia", "Iran", "Britain", "Venice", "Amsterdam"],
            "ORG": ["Five Eyes", "CIA", "MI6"],
        },
    }


@pytest.fixture
def tmp_cache_dir(tmp_path: Path) -> Path:
    """Temporary cache directory for tests."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def mock_yt_dlp(mocker):
    """Mock yt-dlp subprocess calls."""
    mock = mocker.patch("subprocess.run")
    return mock


@pytest.fixture
def mock_ollama(mocker):
    """Mock Ollama client."""
    mock = mocker.patch("wve.synthesize.ollama_generate")
    mock.return_value = {
        "worldview_points": [
            {
                "point": "Test point",
                "elaboration": "Test elaboration",
                "confidence": 0.8,
                "supporting_evidence": ["evidence1"],
            }
        ]
    }
    return mock


# Markers for test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "robustness: tests for noise/edge cases")
    config.addinivalue_line("markers", "quality: tests for extraction/synthesis quality")
    config.addinivalue_line("markers", "integration: end-to-end integration tests")
