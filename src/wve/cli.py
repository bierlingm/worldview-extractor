"""CLI entrypoint for wve (Worldview Extractor)."""

import json
from pathlib import Path

import click

from wve import __version__


@click.group()
@click.version_option(version=__version__, prog_name="wve")
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.pass_context
def main(ctx: click.Context, debug: bool) -> None:
    """Worldview Extractor - Synthesize intellectual worldviews from video appearances."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@main.command()
@click.argument("person")
@click.option("--max-results", "-n", default=10, help="Maximum videos to find")
@click.option("--channel", help="Limit to specific channel URL")
@click.option("--min-duration", default=5, help="Minimum video length in minutes")
@click.option("--max-duration", default=180, help="Maximum video length in minutes")
@click.option("--output", "-o", type=click.Path(), help="Save results to JSON file")
def search(
    person: str,
    max_results: int,
    channel: str | None,
    min_duration: int,
    max_duration: int,
    output: str | None,
) -> None:
    """Discover videos featuring PERSON."""
    from wve.search import save_search_results, search_videos

    click.echo(f"Searching for videos featuring: {person}")
    results = search_videos(
        person,
        max_results=max_results,
        min_duration=min_duration,
        max_duration=max_duration,
        channel=channel,
    )
    click.echo(f"Found {len(results.videos)} videos")

    if output:
        save_search_results(results, output)
        click.echo(f"Saved to {output}")
    else:
        for v in results.videos:
            click.echo(f"  [{v.id}] {v.title} ({v.duration_seconds // 60}m)")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--lang", default="en", help="Preferred language code")
@click.option("--fallback-whisper", is_flag=True, help="Use Whisper if no captions")
@click.option("--output-dir", "-o", type=click.Path(), default="./transcripts", help="Output directory")
def transcripts(input: str, lang: str, fallback_whisper: bool, output_dir: str) -> None:
    """Download and preprocess transcripts from INPUT (URL, ID, or search JSON)."""
    from wve.search import load_search_results
    from wve.transcripts import download_transcripts

    input_path = Path(input)

    # Determine input type
    if input_path.suffix == ".json":
        search_results = load_search_results(input)
        videos = search_results.videos
    else:
        # Assume single URL/ID
        videos = [input]

    click.echo(f"Downloading {len(videos)} transcripts...")
    manifest = download_transcripts(videos, output_dir, lang)
    click.echo(f"Downloaded {len(manifest.transcripts)} transcripts to {output_dir}")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option(
    "--method",
    "-m",
    type=click.Choice(["keywords", "entities", "phrases", "tfidf", "all"]),
    default="all",
    help="Extraction method",
)
@click.option("--top", "-n", default=50, help="Number of items per category")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def extract(input: str, method: str, top: int, output: str | None) -> None:
    """Extract themes, keywords, and entities from transcripts."""
    from wve.extract import (
        extract_all,
        extract_cooccurrences,
        extract_entities_spacy,
        extract_keywords_yake,
        extract_phrases,
        extract_tfidf,
        load_transcripts,
        save_extraction,
    )
    from wve.models import Extraction

    texts, source_ids = load_transcripts(input)
    click.echo(f"Loaded {len(texts)} transcripts")

    if method == "all":
        extraction = extract_all(texts, source_ids, top_n=top)
    else:
        extraction = Extraction(source_transcripts=source_ids)
        if method == "keywords":
            extraction.keywords = extract_keywords_yake(texts, source_ids, top_n=top)
        elif method == "entities":
            extraction.entities = extract_entities_spacy(texts, source_ids)
        elif method == "phrases":
            extraction.phrases = extract_phrases(texts, source_ids, top_n=top)
        elif method == "tfidf":
            extraction.tfidf = extract_tfidf(texts, top_n=top)

    click.echo(f"Extracted: {len(extraction.keywords)} keywords, {len(extraction.tfidf)} TF-IDF terms")

    if output:
        save_extraction(extraction, output)
        click.echo(f"Saved to {output}")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--model", default="all-MiniLM-L6-v2", help="Embedding model")
@click.option("--n-clusters", "-n", default=0, help="Number of clusters (0=auto)")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def cluster(input: str, model: str, n_clusters: int, output: str | None) -> None:
    """Cluster extracted themes into conceptual groups."""
    from wve.cluster import cluster_extraction, save_clusters
    from wve.models import Extraction

    with open(input) as f:
        extraction = Extraction.model_validate_json(f.read())

    click.echo(f"Clustering {len(extraction.keywords) + len(extraction.tfidf)} terms...")
    result = cluster_extraction(extraction, n_clusters=n_clusters, model_name=model)

    click.echo(f"Created {len(result.clusters)} clusters (silhouette: {result.silhouette_score:.2f})")
    for c in result.clusters[:5]:
        click.echo(f"  [{c.id}] {c.label} ({len(c.members)} members)")

    if output:
        save_clusters(result, output)
        click.echo(f"Saved to {output}")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option(
    "--depth",
    "-d",
    type=click.Choice(["quick", "medium", "deep"]),
    default="medium",
    help="Synthesis depth",
)
@click.option("--points", "-n", default=5, help="Number of worldview points")
@click.option("--model", default="llama3", help="Ollama model for deep synthesis")
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--subject", "-s", default="", help="Subject name")
def synthesize(input: str, depth: str, points: int, model: str, output: str | None, subject: str) -> None:
    """Synthesize worldview points from extracted/clustered data."""
    from wve.cluster import load_clusters
    from wve.models import Extraction
    from wve.synthesize import save_worldview
    from wve.synthesize import synthesize as do_synthesize

    # Try loading as clusters first, then as extraction
    input_path = Path(input)
    with open(input_path) as f:
        data = json.load(f)

    if "clusters" in data:
        clusters = load_clusters(input)
        extraction = None
    else:
        extraction = Extraction.model_validate(data)
        from wve.cluster import cluster_extraction

        clusters = cluster_extraction(extraction)

    click.echo(f"Synthesizing at depth: {depth}")
    worldview = do_synthesize(clusters, extraction, subject=subject, depth=depth, n_points=points, model=model)

    click.echo(f"\nWorldview for {worldview.subject or 'Unknown'}:")
    for i, p in enumerate(worldview.points, 1):
        click.echo(f"  {i}. {p.point} (confidence: {p.confidence:.0%})")

    if output:
        save_worldview(worldview, output)
        click.echo(f"\nSaved to {output}")


@main.command()
@click.argument("person")
@click.option(
    "--depth",
    "-d",
    type=click.Choice(["quick", "medium", "deep"]),
    default="medium",
    help="Target depth",
)
@click.option("--max-videos", "-n", default=10, help="Video limit")
@click.option("--output-dir", "-o", type=click.Path(), default="./output", help="Working directory")
@click.option("--cache/--no-cache", default=True, help="Use cached intermediates")
def pipeline(person: str, depth: str, max_videos: int, output_dir: str, cache: bool) -> None:
    """End-to-end pipeline for PERSON."""
    from wve.cluster import cluster_extraction, save_clusters
    from wve.extract import extract_all, load_transcripts, save_extraction
    from wve.search import save_search_results, search_videos
    from wve.synthesize import save_worldview
    from wve.synthesize import synthesize as do_synthesize
    from wve.transcripts import download_transcripts

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Step 1: Search
    click.echo(f"[1/5] Searching for {person}...")
    search_path = out / "search.json"
    search_results = search_videos(person, max_results=max_videos)
    save_search_results(search_results, str(search_path))
    click.echo(f"  Found {len(search_results.videos)} videos")

    # Step 2: Transcripts
    click.echo("[2/5] Downloading transcripts...")
    transcript_dir = out / "transcripts"
    manifest = download_transcripts(search_results.videos, transcript_dir)
    click.echo(f"  Downloaded {len(manifest.transcripts)} transcripts")

    # Step 3: Extract
    click.echo("[3/5] Extracting themes...")
    texts, source_ids = load_transcripts(transcript_dir)
    if not texts:
        click.echo("  No transcripts to process!")
        return
    extraction = extract_all(texts, source_ids)
    save_extraction(extraction, str(out / "extraction.json"))
    click.echo(f"  Extracted {len(extraction.keywords)} keywords")

    # Step 4: Cluster
    click.echo("[4/5] Clustering...")
    clusters = cluster_extraction(extraction)
    save_clusters(clusters, str(out / "clusters.json"))
    click.echo(f"  Created {len(clusters.clusters)} clusters")

    # Step 5: Synthesize
    click.echo(f"[5/5] Synthesizing ({depth})...")
    worldview = do_synthesize(clusters, extraction, subject=person, depth=depth)
    save_worldview(worldview, str(out / "worldview.json"))

    click.echo(f"\n=== Worldview: {person} ===")
    for i, p in enumerate(worldview.points, 1):
        click.echo(f"{i}. {p.point}")
        if p.elaboration:
            click.echo(f"   {p.elaboration}")

    click.echo(f"\nArtifacts saved to: {output_dir}/")


@main.command()
@click.argument("artifact", type=click.Path(exists=True))
def inspect(artifact: str) -> None:
    """Inspect any JSON artifact from previous stages."""
    with open(artifact) as f:
        data = json.load(f)

    # Detect artifact type and display appropriately
    if "videos" in data and "query" in data:
        click.echo(f"Search Results: {data['query']}")
        click.echo(f"Videos: {len(data['videos'])}")
        for v in data["videos"][:10]:
            click.echo(f"  - {v['title'][:60]}... ({v['duration_seconds'] // 60}m)")

    elif "clusters" in data:
        click.echo(f"Cluster Results (silhouette: {data.get('silhouette_score', 0):.2f})")
        for c in data["clusters"]:
            click.echo(f"  [{c['id']}] {c['label']} - {len(c['members'])} members")

    elif "keywords" in data:
        click.echo("Extraction Results")
        click.echo(f"  Keywords: {len(data.get('keywords', []))}")
        click.echo(f"  TF-IDF terms: {len(data.get('tfidf', []))}")
        click.echo(f"  Phrases: {len(data.get('phrases', []))}")
        click.echo(f"  Entities: {len(data.get('entities', {}))}")

    elif "points" in data:
        click.echo(f"Worldview: {data.get('subject', 'Unknown')}")
        click.echo(f"Depth: {data.get('depth', 'unknown')}")
        for i, p in enumerate(data["points"], 1):
            click.echo(f"  {i}. {p['point']} ({p['confidence']:.0%})")

    else:
        click.echo(json.dumps(data, indent=2)[:2000])


if __name__ == "__main__":
    main()
