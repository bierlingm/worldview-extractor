"""Video search via yt-dlp."""

import json
import subprocess
from datetime import datetime

from wve.models import SearchResult, VideoMetadata


def search_videos(
    query: str,
    max_results: int = 10,
    min_duration: int = 5,
    max_duration: int = 180,
    channel: str | None = None,
) -> SearchResult:
    """Search for videos featuring a person using yt-dlp.

    Args:
        query: Search term (typically a person's name)
        max_results: Maximum number of videos to return
        min_duration: Minimum video duration in minutes
        max_duration: Maximum video duration in minutes
        channel: Optional channel URL to limit search

    Returns:
        SearchResult containing video metadata
    """
    search_query = f"ytsearch{max_results}:{query}"
    if channel:
        search_query = f"{channel}/search?query={query}"

    cmd = [
        "yt-dlp",
        search_query,
        "--dump-json",
        "--flat-playlist",
        "--no-warnings",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")

    videos: list[VideoMetadata] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        duration = data.get("duration") or 0
        duration_minutes = duration / 60

        if duration_minutes < min_duration or duration_minutes > max_duration:
            continue

        # Parse upload date
        upload_date = data.get("upload_date", "")
        if upload_date and len(upload_date) == 8:
            published = datetime.strptime(upload_date, "%Y%m%d")
        else:
            published = datetime.now()

        video = VideoMetadata(
            id=data.get("id", ""),
            title=data.get("title", ""),
            channel=data.get("channel", data.get("uploader", "")),
            channel_id=data.get("channel_id", data.get("uploader_id", "")),
            duration_seconds=duration,
            url=data.get("webpage_url", f"https://www.youtube.com/watch?v={data.get('id', '')}"),
            published=published,
        )
        videos.append(video)

    return SearchResult(
        query=query,
        max_results=max_results,
        videos=videos,
    )


def save_search_results(results: SearchResult, output_path: str) -> None:
    """Save search results to a JSON file."""
    with open(output_path, "w") as f:
        f.write(results.model_dump_json(indent=2))


def load_search_results(input_path: str) -> SearchResult:
    """Load search results from a JSON file."""
    with open(input_path) as f:
        return SearchResult.model_validate_json(f.read())
