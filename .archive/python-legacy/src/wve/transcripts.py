"""Transcript download and preprocessing via yt-dlp."""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from wve.models import TranscriptManifest, VideoMetadata


def download_transcript(
    video_url: str,
    output_dir: Path,
    lang: str = "en",
) -> Path | None:
    """Download transcript for a single video.

    Args:
        video_url: YouTube video URL or ID
        output_dir: Directory to save transcript
        lang: Preferred language code

    Returns:
        Path to transcript file, or None if unavailable
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract video ID for filename
    video_id = video_url
    if "youtube.com" in video_url or "youtu.be" in video_url:
        match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", video_url)
        if match:
            video_id = match.group(1)

    output_template = str(output_dir / f"{video_id}")

    cmd = [
        "yt-dlp",
        video_url,
        "--write-auto-sub",
        "--sub-lang", lang,
        "--skip-download",
        "--output", output_template,
        "--no-warnings",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    # Look for downloaded VTT file
    vtt_files = list(output_dir.glob(f"{video_id}*.vtt"))
    if not vtt_files:
        return None

    vtt_path = vtt_files[0]
    txt_path = output_dir / f"{video_id}.txt"

    # Convert VTT to plain text
    clean_text = vtt_to_text(vtt_path.read_text())
    txt_path.write_text(clean_text)

    # Remove VTT file
    vtt_path.unlink()

    return txt_path


def vtt_to_text(vtt_content: str) -> str:
    """Convert VTT subtitle content to clean plain text.

    Handles YouTube's rolling caption deduplication.
    """
    lines = []
    seen_lines: set[str] = set()

    for line in vtt_content.split("\n"):
        # Skip VTT headers and timestamps
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}", line):
            continue
        if "-->" in line:
            continue
        if not line.strip():
            continue

        # Remove VTT formatting tags
        clean = re.sub(r"<[^>]+>", "", line)
        clean = clean.strip()

        if not clean:
            continue

        # Deduplicate (YouTube rolling captions repeat lines)
        if clean not in seen_lines:
            seen_lines.add(clean)
            lines.append(clean)

    return " ".join(lines)


def download_transcripts(
    videos: list[VideoMetadata] | list[str],
    output_dir: str | Path,
    lang: str = "en",
) -> TranscriptManifest:
    """Download transcripts for multiple videos.

    Args:
        videos: List of VideoMetadata objects or video URLs
        output_dir: Directory to save transcripts
        lang: Preferred language code

    Returns:
        TranscriptManifest with paths to downloaded transcripts
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    transcripts: dict[str, Path] = {}
    video_metadata: list[VideoMetadata] = []

    for video in videos:
        if isinstance(video, str):
            url = video
            video_id = url
            if "youtube.com" in url or "youtu.be" in url:
                match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
                if match:
                    video_id = match.group(1)
            # Create minimal metadata for URL-only input
            meta = VideoMetadata(
                id=video_id,
                title="",
                channel="",
                channel_id="",
                duration_seconds=0,
                url=url,
                published=datetime.now(),
            )
        else:
            meta = video
            url = meta.url

        transcript_path = download_transcript(url, output_path, lang)
        if transcript_path:
            transcripts[meta.id] = transcript_path
            video_metadata.append(meta)

    manifest = TranscriptManifest(
        videos=video_metadata,
        transcripts=transcripts,
    )

    # Save manifest
    manifest_path = output_path / "manifest.json"
    with open(manifest_path, "w") as f:
        f.write(manifest.model_dump_json(indent=2))

    return manifest


def load_manifest(manifest_path: str | Path) -> TranscriptManifest:
    """Load a transcript manifest from JSON."""
    with open(manifest_path) as f:
        return TranscriptManifest.model_validate_json(f.read())
