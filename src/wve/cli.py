"""CLI entrypoint for wve (Worldview Extractor)."""

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
    click.echo(f"Searching for videos featuring: {person}")
    # TODO: Implement in search.py


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--lang", default="en", help="Preferred language code")
@click.option("--fallback-whisper", is_flag=True, help="Use Whisper if no captions")
@click.option("--output-dir", "-o", type=click.Path(), default="./transcripts", help="Output directory")
def transcripts(input: str, lang: str, fallback_whisper: bool, output_dir: str) -> None:
    """Download and preprocess transcripts from INPUT (URL, ID, or search JSON)."""
    click.echo(f"Downloading transcripts from: {input}")
    # TODO: Implement in transcripts.py


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
    click.echo(f"Extracting from: {input} using method: {method}")
    # TODO: Implement in extract.py


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--model", default="all-MiniLM-L6-v2", help="Embedding model")
@click.option("--n-clusters", "-n", default=0, help="Number of clusters (0=auto)")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def cluster(input: str, model: str, n_clusters: int, output: str | None) -> None:
    """Cluster extracted themes into conceptual groups."""
    click.echo(f"Clustering: {input}")
    # TODO: Implement in cluster.py


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
def synthesize(input: str, depth: str, points: int, model: str, output: str | None) -> None:
    """Synthesize worldview points from extracted/clustered data."""
    click.echo(f"Synthesizing from: {input} at depth: {depth}")
    # TODO: Implement in synthesize.py


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
    click.echo(f"Running pipeline for: {person} at depth: {depth}")
    # TODO: Implement in pipeline.py


@main.command()
@click.argument("artifact", type=click.Path(exists=True))
def inspect(artifact: str) -> None:
    """Inspect any JSON artifact from previous stages."""
    click.echo(f"Inspecting: {artifact}")
    # TODO: Implement artifact inspection


if __name__ == "__main__":
    main()
