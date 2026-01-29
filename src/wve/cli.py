"""CLI entrypoint for Weave - Comprehensive worldview synthesis tool."""

import json
from pathlib import Path

import click

from wve import __version__


@click.group()
@click.version_option(version=__version__, prog_name="wve")
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.pass_context
def main(ctx: click.Context, debug: bool) -> None:
    """Weave - Synthesize intellectual worldviews from arbitrary text sources."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


# === Primary Entry Point ===


@main.command()
@click.argument("input", nargs=-1, required=False)
@click.option("--subject", "-s", required=True, help="Subject name for the worldview")
@click.option("--output", "-o", type=click.Path(), help="Save to local directory instead of store")
@click.option("--url", "-u", multiple=True, help="Additional URL(s) to include")
@click.option("--lang", default="en", help="Transcript language")
@click.option("--force", is_flag=True, help="Re-download even if transcripts exist")
@click.option("--fetch-only", is_flag=True, help="Download transcripts only, no analysis")
@click.option("--report-only", is_flag=True, help="Analyze existing transcripts only")
@click.option("--json", "as_json", is_flag=True, help="Output report as JSON")
def run(
    input: tuple[str, ...],
    subject: str,
    output: str | None,
    url: tuple[str, ...],
    lang: str,
    force: bool,
    fetch_only: bool,
    report_only: bool,
    as_json: bool,
) -> None:
    """Build your worldview library from any source.

    Every run is automatically saved to your library (~/.wve/store/).
    Use -o to save to a local directory instead.

    INPUT can be:
    \b
      - YouTube URLs      https://youtube.com/watch?v=...
      - URL list files    urls.txt (one URL per line)
      - Transcript files  transcript.txt, notes.md
      - Directories       ./transcripts/

    \b
    Examples:
      wve run https://youtu.be/xyz -s "Naval Ravikant"
      wve run urls.txt -s "Naval Ravikant"
      wve run -u URL1 -u URL2 -s "Naval Ravikant"
      wve run ./transcripts/ -s "Naval" --report-only

    \b
    After running:
      wve store list              List all worldviews
      wve store show <slug>       View a worldview
      wve store delete <slug>     Remove a worldview
    """
    import re
    import shutil
    from collections import Counter
    from datetime import datetime
    from pathlib import Path

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from wve.identity import extract_video_id, slugify
    from wve.quotes import extract_quotes_from_dir
    from wve.store import WorldviewEntry, get_entry_dir, get_store_dir, load_entry, save_entry
    from wve.transcripts import download_transcript

    console = Console(stderr=True)

    # Generate slug from subject
    slug = slugify(subject)

    # Determine output location
    use_store = output is None
    if use_store:
        output_path = get_entry_dir(slug)
    else:
        output_path = Path(output)

    transcripts_dir = output_path / "transcripts"

    # Collect all inputs
    all_inputs = list(input) + list(url)

    # === Input Validation ===
    if not all_inputs and not report_only:
        console.print()
        console.print("[red bold]No input provided[/red bold]")
        console.print()
        console.print("Provide sources using positional arguments or --url flags:")
        console.print()
        console.print("  [cyan]wve run[/cyan] [green]https://youtu.be/xyz[/green] [yellow]-s \"Person Name\"[/yellow]")
        console.print("  [cyan]wve run[/cyan] [green]urls.txt[/green] [yellow]-s \"Person Name\"[/yellow]")
        console.print("  [cyan]wve run[/cyan] [yellow]-u[/yellow] [green]URL1[/green] [yellow]-u[/yellow] [green]URL2[/green] [yellow]-s \"Person Name\"[/yellow]")
        console.print()
        raise SystemExit(1)

    # === Input Classification ===
    def classify_input(inp: str) -> str:
        """Return 'url', 'file', 'dir', or 'url_list'."""
        if inp.startswith(("http://", "https://")):
            return "url"
        p = Path(inp)
        if p.is_dir():
            return "dir"
        if p.is_file():
            try:
                content = p.read_text()
                lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#")]
                if lines and all(l.startswith(("http://", "https://")) for l in lines[:5]):
                    return "url_list"
            except Exception:
                pass
            return "file"
        return "unknown"

    urls_to_fetch: list[str] = []
    local_files: list[Path] = []
    existing_transcript_dir: Path | None = None

    for inp in all_inputs:
        inp_type = classify_input(inp)
        if inp_type == "url":
            urls_to_fetch.append(inp)
        elif inp_type == "url_list":
            with open(inp) as f:
                url_count = 0
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls_to_fetch.append(line)
                        url_count += 1
            if not as_json:
                console.print(f"[dim]Loaded {url_count} URLs from {inp}[/dim]")
        elif inp_type == "dir":
            existing_transcript_dir = Path(inp)
            if not as_json:
                txt_count = len(list(existing_transcript_dir.glob("*.txt")))
                console.print(f"[dim]Found directory with {txt_count} transcript(s)[/dim]")
        elif inp_type == "file":
            local_files.append(Path(inp))
        else:
            console.print()
            console.print(f"[yellow bold]Unknown input:[/yellow bold] {inp}")
            console.print()
            if not Path(inp).exists():
                console.print(f"  File or directory does not exist: [red]{inp}[/red]")
                console.print()
                console.print("  Did you mean to provide a URL? Make sure it starts with http:// or https://")
            else:
                console.print(f"  Could not determine input type for: {inp}")
            console.print()

    # === Report-Only Mode ===
    if report_only:
        if existing_transcript_dir:
            transcripts_dir = existing_transcript_dir
        elif transcripts_dir.exists() and list(transcripts_dir.glob("*.txt")):
            pass  # Use existing transcripts in output dir
        else:
            console.print()
            console.print("[red bold]No transcripts found for --report-only[/red bold]")
            console.print()
            console.print("Provide a directory containing transcript files:")
            console.print()
            console.print("  [cyan]wve run[/cyan] [green]./transcripts/[/green] [yellow]-s \"Person\" --report-only[/yellow]")
            console.print()
            console.print("Or run without --report-only to download transcripts first:")
            console.print()
            console.print("  [cyan]wve run[/cyan] [green]https://youtu.be/xyz[/green] [yellow]-s \"Person\"[/yellow]")
            console.print()
            raise SystemExit(1)
    else:
        # Create output directories
        output_path.mkdir(parents=True, exist_ok=True)
        transcripts_dir.mkdir(parents=True, exist_ok=True)

        # === Resume Logic ===
        existing_transcripts = list(transcripts_dir.glob("*.txt"))
        if existing_transcripts and not force:
            if not as_json:
                console.print()
                console.print(f"[cyan]Found {len(existing_transcripts)} existing transcript(s)[/cyan]")
                console.print("[dim]Skipping download. Use --force to re-download.[/dim]")
        else:
            # === Download Transcripts ===
            if urls_to_fetch:
                if not as_json:
                    console.print()
                    console.print(f"[bold]Downloading {len(urls_to_fetch)} transcript(s)...[/bold]")

                from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

                succeeded = []
                failed = []

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=console,
                    disable=as_json,
                ) as progress:
                    task = progress.add_task("Fetching transcripts...", total=len(urls_to_fetch))
                    for video_url in urls_to_fetch:
                        vid_id = "unknown"
                        try:
                            vid_id = extract_video_id(video_url)
                            progress.update(task, description=f"[dim]{vid_id}[/dim]")
                        except Exception:
                            progress.update(task, description=f"[dim]{video_url[:30]}...[/dim]")

                        result = download_transcript(video_url, transcripts_dir, lang)
                        if result:
                            succeeded.append(vid_id)
                        else:
                            failed.append((vid_id, video_url))
                        progress.advance(task)

                if not as_json:
                    if succeeded:
                        console.print(f"[green]✓ Downloaded {len(succeeded)} transcript(s)[/green]")
                    if failed:
                        console.print()
                        console.print(f"[yellow bold]⚠ Failed to download {len(failed)} transcript(s)[/yellow bold]")
                        console.print()
                        for vid_id, url in failed[:5]:
                            console.print(f"  [dim]•[/dim] {vid_id}: No captions available")
                        if len(failed) > 5:
                            console.print(f"  [dim]... and {len(failed) - 5} more[/dim]")
                        console.print()
                        console.print("[dim]Tip: Some videos don't have captions. Try videos with [CC] indicator.[/dim]")

            # === Copy Local Files ===
            if local_files:
                for lf in local_files:
                    dest = transcripts_dir / lf.name
                    if not dest.exists() or force:
                        shutil.copy(lf, dest)
                if not as_json:
                    console.print(f"[green]✓ Copied {len(local_files)} local file(s)[/green]")

            # === Copy from Existing Directory ===
            if existing_transcript_dir and existing_transcript_dir != transcripts_dir:
                copied = 0
                for f in existing_transcript_dir.glob("*.txt"):
                    shutil.copy(f, transcripts_dir / f.name)
                    copied += 1
                if not as_json and copied:
                    console.print(f"[green]✓ Copied {copied} transcript(s) from {existing_transcript_dir}[/green]")

    # === Fetch-Only Mode ===
    if fetch_only:
        count = len(list(transcripts_dir.glob("*.txt")))
        if as_json:
            click.echo(json.dumps({"transcripts_dir": str(transcripts_dir), "count": count, "slug": slug}))
        else:
            console.print()
            console.print(Panel(
                f"[green bold]Downloaded {count} transcript(s)[/green bold]\n\n"
                f"Location: [cyan]{transcripts_dir}[/cyan]\n\n"
                f"[dim]To analyze these transcripts:[/dim]\n"
                f"  wve run {transcripts_dir} -s \"{subject}\" --report-only",
                title="Fetch Complete",
                border_style="green",
            ))
        return

    # === Verify Transcripts Exist ===
    transcript_files = list(transcripts_dir.glob("*.txt"))
    if not transcript_files:
        console.print()
        console.print("[red bold]No transcripts to analyze[/red bold]")
        console.print()
        if urls_to_fetch:
            console.print("All transcript downloads failed. Possible causes:")
            console.print()
            console.print("  • Videos don't have captions enabled")
            console.print("  • Videos are private or age-restricted")
            console.print("  • Network connectivity issues")
            console.print()
            console.print("[dim]Tip: Try different videos, or provide local transcript files.[/dim]")
        else:
            console.print("No sources provided that could be analyzed.")
            console.print()
            console.print("Provide YouTube URLs or local transcript files:")
            console.print()
            console.print("  [cyan]wve run[/cyan] [green]https://youtu.be/xyz[/green] [yellow]-s \"Person\"[/yellow]")
        console.print()
        raise SystemExit(1)

    # === Analysis Phase ===
    if not as_json:
        console.print()
        console.print(f"[bold]Analyzing {len(transcript_files)} transcript(s)...[/bold]")

    collection = extract_quotes_from_dir(transcripts_dir, max_quotes=100, min_score=0.2)

    # === Theme Extraction ===
    word_counts: Counter[str] = Counter()
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                 "have", "has", "had", "do", "does", "did", "will", "would", "could",
                 "should", "may", "might", "must", "shall", "can", "to", "of", "in",
                 "for", "on", "with", "at", "by", "from", "as", "or", "and", "but",
                 "if", "then", "so", "than", "that", "this", "these", "those", "it",
                 "its", "you", "your", "i", "my", "me", "we", "our", "they", "their",
                 "it's", "don't", "doesn't", "didn't", "won't", "wouldn't", "can't",
                 "couldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't",
                 "haven't", "hasn't", "hadn't", "that's", "there's", "here's",
                 "what's", "who's", "he's", "she's", "let's", "how's", "where's",
                 "think", "know", "really", "just", "going", "people", "thing",
                 "things", "like", "about", "what", "when", "where", "which", "there",
                 "been", "very", "much", "more", "some", "only", "other", "into",
                 "said", "says", "saying", "want", "wants", "wanted", "need", "make",
                 "made", "take", "took", "come", "came", "give", "gave", "look", "also"}

    for quote in collection.quotes:
        words = re.findall(r"[a-z]+(?:'[a-z]+)?", quote.text.lower())
        meaningful = [w for w in words if len(w) > 3 and w not in stopwords]
        word_counts.update(meaningful)

    top_themes = word_counts.most_common(10)
    contrarian = [q for q in collection.quotes if q.is_contrarian]

    # === Generate Report ===
    report_lines = [
        f"# Worldview: {subject}",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"- **Sources:** {collection.source_count}",
        f"- **Quotes:** {len(collection.quotes)}",
        f"- **Contrarian views:** {len(contrarian)}",
        "",
        "## Themes",
        "",
    ]
    for word, count in top_themes:
        report_lines.append(f"- **{word.title()}** ({count}x)")

    report_lines.extend(["", "## Notable Quotes", ""])
    for i, q in enumerate(collection.quotes[:15], 1):
        report_lines.append(f'{i}. "{q.text}"')
        report_lines.append(f"   *— {q.source_id}*")
        report_lines.append("")

    if contrarian:
        report_lines.extend(["", "## Contrarian Views", ""])
        for i, q in enumerate(contrarian[:10], 1):
            report_lines.append(f'{i}. "{q.text}"')
            report_lines.append(f"   *— {q.source_id}*")
            report_lines.append("")

    report_text = "\n".join(report_lines)
    report_path = output_path / "report.md"
    report_path.write_text(report_text)

    # === Save to Store ===
    if use_store:
        entry = WorldviewEntry(
            slug=slug,
            display_name=subject,
            source_count=collection.source_count,
            quote_count=len(collection.quotes),
            themes=[{"name": w.title(), "count": c} for w, c in top_themes],
            top_quotes=[q.model_dump() for q in collection.quotes[:20]],
            contrarian_quotes=[q.model_dump() for q in contrarian[:15]],
            transcripts_dir=str(transcripts_dir),
            report_path=str(report_path),
        )
        save_entry(entry)

    # === JSON Output ===
    if as_json:
        result = {
            "subject": subject,
            "slug": slug,
            "generated_at": datetime.now().isoformat(),
            "source_count": collection.source_count,
            "total_quotes": len(collection.quotes),
            "themes": [{"name": w.title(), "count": c} for w, c in top_themes],
            "top_quotes": [q.model_dump() for q in collection.quotes[:20]],
            "contrarian_quotes": [q.model_dump() for q in contrarian[:15]],
            "report_path": str(report_path),
            "transcripts_dir": str(transcripts_dir),
            "stored": use_store,
        }
        click.echo(json.dumps(result, indent=2, default=str))
        return

    # === Success Output ===
    console.print()

    # Summary panel
    theme_str = ", ".join(w.title() for w, _ in top_themes[:5])
    if use_store:
        location_info = f"[bold]Stored as:[/bold] [cyan]{slug}[/cyan]"
    else:
        location_info = f"[bold]Saved to:[/bold] [cyan]{output_path}[/cyan]"

    console.print(Panel(
        f"[green bold]{subject}[/green bold]\n\n"
        f"[bold]Sources:[/bold] {collection.source_count} transcript(s)\n"
        f"[bold]Quotes:[/bold] {len(collection.quotes)} notable quotes\n"
        f"[bold]Contrarian:[/bold] {len(contrarian)} distinctive views\n"
        f"[bold]Themes:[/bold] {theme_str}\n\n"
        f"{location_info}",
        title="[green]✓ Worldview Extracted[/green]",
        border_style="green",
    ))

    # Top quotes preview
    if collection.quotes:
        console.print()
        console.print("[bold]Top quotes:[/bold]")
        for i, q in enumerate(collection.quotes[:3], 1):
            text = q.text[:100] + "..." if len(q.text) > 100 else q.text
            console.print(f"  [dim]{i}.[/dim] \"{text}\"")

    # Next steps
    console.print()
    console.print("[dim]─────────────────────────────────────────[/dim]")
    console.print()
    console.print("[bold]What's next?[/bold]")
    console.print()

    if use_store:
        console.print(f"  [cyan]wve store show {slug}[/cyan]       View full details")
        console.print(f"  [cyan]wve ask {transcripts_dir} \"question\"[/cyan]")
        console.print(f"                              Ask questions about the content")
        console.print(f"  [cyan]cat {report_path}[/cyan]")
        console.print(f"                              Read the full report")
        console.print()
        console.print(f"  [cyan]wve store list[/cyan]            See all your worldviews")
        console.print(f"  [cyan]wve store delete {slug}[/cyan]    Remove this worldview")
    else:
        console.print(f"  [cyan]cat {report_path}[/cyan]")
        console.print(f"                              Read the full report")
        console.print(f"  [cyan]wve ask {transcripts_dir} \"question\"[/cyan]")
        console.print(f"                              Ask questions about the content")

    console.print()


# === Identity Commands (v0.2) ===


@main.group()
def identity() -> None:
    """Manage subject identities (v0.2)."""
    pass


@identity.command("create")
@click.argument("name")
@click.option("--slug", "-s", help="Custom slug (default: derived from name)")
@click.option("--channel", "-c", help="YouTube channel URL")
@click.option("--website", "-w", help="Personal website URL")
@click.option("--alias", "-a", multiple=True, help="Alternative names")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def identity_create(
    name: str,
    slug: str | None,
    channel: str | None,
    website: str | None,
    alias: tuple[str, ...],
    as_json: bool,
) -> None:
    """Create a new identity profile for NAME."""
    from wve.identity import create_identity

    try:
        identity = create_identity(
            display_name=name,
            slug=slug,
            aliases=list(alias) if alias else None,
            channel_url=channel,
            website=website,
        )

        if as_json:
            click.echo(identity.model_dump_json(indent=2))
        else:
            click.echo(f"Created identity: {identity.slug}")
            click.echo(f"  Name: {identity.display_name}")
            if identity.aliases:
                click.echo(f"  Aliases: {', '.join(identity.aliases)}")
            if identity.channels:
                click.echo(f"  Channels: {len(identity.channels)}")
            if identity.websites:
                click.echo(f"  Website: {identity.websites[0]}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@identity.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def identity_list(as_json: bool) -> None:
    """List all known identities."""
    from wve.identity import list_identities

    identities = list_identities()

    if as_json:
        click.echo(json.dumps([i.model_dump() for i in identities], indent=2, default=str))
    elif not identities:
        click.echo("No identities found. Create one with: wve identity create <name>")
    else:
        for i in identities:
            channels = len(i.channels)
            confirmed = len(i.confirmed_videos)
            click.echo(f"{i.slug:20} {i.display_name:25} {channels} channel(s), {confirmed} confirmed")


@identity.command("show")
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def identity_show(slug: str, as_json: bool) -> None:
    """Show details for identity SLUG."""
    from wve.identity import load_identity

    try:
        identity = load_identity(slug)

        if as_json:
            click.echo(identity.model_dump_json(indent=2))
        else:
            click.echo(f"Identity: {identity.display_name}")
            click.echo(f"  Slug: {identity.slug}")
            if identity.aliases:
                click.echo(f"  Aliases: {', '.join(identity.aliases)}")
            click.echo(f"  Created: {identity.created_at.strftime('%Y-%m-%d')}")
            click.echo(f"  Updated: {identity.updated_at.strftime('%Y-%m-%d')}")

            if identity.channels:
                click.echo("\n  Channels:")
                for ch in identity.channels:
                    v = " (verified)" if ch.verified else ""
                    click.echo(f"    - {ch.url}{v}")

            if identity.websites:
                click.echo(f"\n  Websites: {', '.join(identity.websites)}")

            click.echo(f"\n  Confirmed videos: {len(identity.confirmed_videos)}")
            click.echo(f"  Rejected videos: {len(identity.rejected_videos)}")
            click.echo(f"  Trusted channels: {len(identity.trusted_channels)}")
    except FileNotFoundError:
        click.echo(f"Identity not found: {slug}", err=True)
        raise SystemExit(1)


@identity.command("add-channel")
@click.argument("slug")
@click.argument("url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def identity_add_channel(slug: str, url: str, as_json: bool) -> None:
    """Add a YouTube channel URL to identity SLUG."""
    from wve.identity import add_channel_to_identity

    try:
        identity = add_channel_to_identity(slug, url)

        if as_json:
            click.echo(identity.model_dump_json(indent=2))
        else:
            click.echo(f"Added channel to {identity.display_name}")
            click.echo(f"  Total channels: {len(identity.channels)}")
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@identity.command("add-video")
@click.argument("slug")
@click.argument("video", nargs=-1, required=True)
@click.option("--reject", is_flag=True, help="Mark as rejected instead of confirmed")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def identity_add_video(slug: str, video: tuple[str, ...], reject: bool, as_json: bool) -> None:
    """Add confirmed (or rejected) video(s) to identity SLUG."""
    from wve.identity import add_video_to_identity, extract_video_id

    try:
        for v in video:
            vid = extract_video_id(v)
            identity = add_video_to_identity(slug, vid, confirmed=not reject)

        if as_json:
            click.echo(identity.model_dump_json(indent=2))
        else:
            action = "rejected" if reject else "confirmed"
            click.echo(f"Added {len(video)} {action} video(s) to {identity.display_name}")
            click.echo(f"  Confirmed: {len(identity.confirmed_videos)}")
            click.echo(f"  Rejected: {len(identity.rejected_videos)}")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@identity.command("delete")
@click.argument("slug")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def identity_delete(slug: str, yes: bool, as_json: bool) -> None:
    """Delete identity SLUG."""
    from wve.identity import delete_identity, load_identity

    try:
        identity = load_identity(slug)
    except FileNotFoundError:
        click.echo(f"Identity not found: {slug}", err=True)
        raise SystemExit(1)

    if not yes and not as_json:
        if not click.confirm(f"Delete identity '{identity.display_name}'?"):
            click.echo("Cancelled.")
            return

    delete_identity(slug)

    if as_json:
        click.echo(json.dumps({"deleted": slug, "success": True}))
    else:
        click.echo(f"Deleted: {slug}")


# === Discovery Commands (v0.2) ===


@main.command()
@click.argument("query")
@click.option("--max-results", "-n", default=20, help="Maximum videos to search")
@click.option("--identity", "-i", "identity_slug", help="Use existing identity for context")
@click.option("--channel", "-c", help="Filter to specific channel URL")
@click.option("--min-duration", default=5, help="Minimum video length in minutes")
@click.option("--max-duration", default=180, help="Maximum video length in minutes")
@click.option("--output", "-o", type=click.Path(), help="Save candidates to JSON file")
@click.option("--strict", is_flag=True, help="Only include videos with full query in title")
@click.option("--auto-classify", is_flag=True, help="Auto-classify candidates (for scripting)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON (for automation)")
def discover(
    query: str,
    max_results: int,
    identity_slug: str | None,
    channel: str | None,
    min_duration: int,
    max_duration: int,
    output: str | None,
    strict: bool,
    auto_classify: bool,
    as_json: bool,
) -> None:
    """Search for videos WITHOUT downloading - returns candidates for confirmation.
    
    Unlike 'search', this classifies candidates as likely/uncertain/false_positive
    and supports identity-based context for better accuracy.
    """
    from rich.console import Console
    from rich.table import Table

    from wve.classify import CandidateSet, VideoCandidate, classify_candidates
    from wve.identity import load_identity
    from wve.search import search_videos

    console = Console(stderr=True)
    identity = None

    # Load identity if provided
    if identity_slug:
        try:
            identity = load_identity(identity_slug)
            if not as_json:
                console.print(f"Using identity: {identity.display_name}")
        except FileNotFoundError:
            console.print(f"[red]Identity not found: {identity_slug}[/red]")
            raise SystemExit(1)

    # Search
    if not as_json:
        console.print(f"Searching for: {query}...")

    results = search_videos(
        query,
        max_results=max_results,
        min_duration=min_duration,
        max_duration=max_duration,
        channel=channel,
    )

    # Convert to candidates
    candidates = [
        VideoCandidate(
            id=v.id,
            title=v.title,
            channel=v.channel,
            channel_id=v.channel_id,
            duration_seconds=v.duration_seconds,
            url=v.url,
            published=v.published,
        )
        for v in results.videos
    ]

    # Apply strict filter
    if strict:
        query_lower = query.lower()
        candidates = [c for c in candidates if query_lower in c.title.lower()]

    # Classify
    classify_candidates(candidates, query, identity)

    # Build candidate set
    candidate_set = CandidateSet(
        query=query,
        identity_slug=identity_slug,
        candidates=candidates,
    )

    # Output
    if as_json:
        click.echo(candidate_set.model_dump_json(indent=2))
    else:
        # Group by classification
        likely = [c for c in candidates if c.classification == "likely"]
        uncertain = [c for c in candidates if c.classification == "uncertain"]
        false_pos = [c for c in candidates if c.classification == "false_positive"]

        console.print(f"\nFound {len(candidates)} candidates for \"{query}\"\n")

        if likely:
            console.print("[green bold]LIKELY MATCHES[/green bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", width=50)
            table.add_column("Channel", width=20)
            table.add_column("Duration", width=8)
            table.add_column("Confidence", width=10)

            for i, c in enumerate(likely, 1):
                dur = f"{c.duration_seconds // 60}m"
                conf = f"{c.confidence:.0%}"
                table.add_row(str(i), c.title[:50], c.channel[:20], dur, conf)
            console.print(table)
            console.print()

        if uncertain:
            console.print("[yellow bold]UNCERTAIN[/yellow bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", width=50)
            table.add_column("Channel", width=20)
            table.add_column("Reason", width=30)

            for i, c in enumerate(uncertain, len(likely) + 1):
                table.add_row(str(i), c.title[:50], c.channel[:20], c.classification_reason or "")
            console.print(table)
            console.print()

        if false_pos:
            console.print("[red bold]FALSE POSITIVES[/red bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", width=50)
            table.add_column("Reason", width=40)

            for i, c in enumerate(false_pos, len(likely) + len(uncertain) + 1):
                table.add_row(str(i), c.title[:50], c.classification_reason or "")
            console.print(table)
            console.print()

        console.print(f"[dim]Summary: {len(likely)} likely, {len(uncertain)} uncertain, {len(false_pos)} false positives[/dim]")

        if output:
            with open(output, "w") as f:
                f.write(candidate_set.model_dump_json(indent=2))
            console.print(f"\nSaved to: {output}")
        else:
            console.print("\n[dim]Use --output/-o to save candidates for confirmation[/dim]")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--identity", "-i", "identity_slug", help="Save confirmations to identity")
@click.option("--output", "-o", type=click.Path(), help="Save confirmed candidates to JSON")
@click.option("--accept", "accept_ids", help="Comma-separated indices to accept (1-based)")
@click.option("--reject", "reject_ids", help="Comma-separated indices to reject (1-based)")
@click.option("--accept-likely", is_flag=True, help="Auto-accept all 'likely' candidates")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def confirm(
    input: str,
    identity_slug: str | None,
    output: str | None,
    accept_ids: str | None,
    reject_ids: str | None,
    accept_likely: bool,
    yes: bool,
    as_json: bool,
) -> None:
    """Confirm or reject video candidates from a candidates.json file.
    
    Interactive mode (default): prompts for each candidate.
    Batch mode: use --accept and --reject with comma-separated indices.
    """
    from pathlib import Path

    from rich.console import Console
    from rich.prompt import Confirm, Prompt
    from rich.table import Table

    from wve.classify import CandidateSet, update_identity_from_feedback
    from wve.identity import load_identity, save_identity

    console = Console(stderr=True)

    # Load candidates
    with open(input) as f:
        candidate_set = CandidateSet.model_validate_json(f.read())

    candidates = candidate_set.candidates
    if not candidates:
        if as_json:
            click.echo(json.dumps({"confirmed": [], "rejected": [], "count": 0}))
        else:
            console.print("[yellow]No candidates to confirm[/yellow]")
        return

    # Load identity if provided
    identity = None
    if identity_slug:
        try:
            identity = load_identity(identity_slug)
        except FileNotFoundError:
            console.print(f"[red]Identity not found: {identity_slug}[/red]")
            raise SystemExit(1)
    elif candidate_set.identity_slug:
        try:
            identity = load_identity(candidate_set.identity_slug)
            identity_slug = candidate_set.identity_slug
        except FileNotFoundError:
            pass

    # Parse accept/reject indices
    def parse_indices(s: str | None) -> set[int]:
        if not s:
            return set()
        indices = set()
        for part in s.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                indices.update(range(int(start), int(end) + 1))
            else:
                indices.add(int(part))
        return indices

    accept_set = parse_indices(accept_ids)
    reject_set = parse_indices(reject_ids)

    # Batch mode or interactive
    is_batch = bool(accept_ids or reject_ids or accept_likely)

    if is_batch:
        # Batch mode
        for i, c in enumerate(candidates, 1):
            if accept_likely and c.classification == "likely":
                c.confirmed = True
                c.rejected = False
            elif i in accept_set:
                c.confirmed = True
                c.rejected = False
            elif i in reject_set:
                c.confirmed = False
                c.rejected = True
    else:
        # Interactive mode
        if as_json:
            console.print("[red]Interactive mode not supported with --json. Use --accept/--reject.[/red]")
            raise SystemExit(1)

        console.print(f"\nConfirming {len(candidates)} candidates for \"{candidate_set.query}\"\n")
        console.print("[dim]Enter: y=yes, n=no, s=skip, q=quit[/dim]\n")

        for i, c in enumerate(candidates, 1):
            # Show candidate info
            dur = f"{c.duration_seconds // 60}m"
            cls_color = {"likely": "green", "uncertain": "yellow", "false_positive": "red"}.get(
                c.classification or "", "white"
            )
            console.print(
                f"[bold][{i}/{len(candidates)}][/bold] [{cls_color}]{c.classification or 'unknown'}[/{cls_color}]"
            )
            console.print(f"  Title: {c.title}")
            console.print(f"  Channel: {c.channel} | Duration: {dur}")
            console.print(f"  URL: {c.url}")
            if c.classification_reason:
                console.print(f"  [dim]Reason: {c.classification_reason}[/dim]")

            choice = Prompt.ask("  Confirm?", choices=["y", "n", "s", "q"], default="s")

            if choice == "y":
                c.confirmed = True
                c.rejected = False
            elif choice == "n":
                c.confirmed = False
                c.rejected = True
            elif choice == "q":
                console.print("[yellow]Quit early[/yellow]")
                break
            # s = skip, leave as-is

            console.print()

    # Update identity with feedback
    if identity:
        for c in candidates:
            if c.confirmed is True:
                update_identity_from_feedback(identity, c, confirmed=True)
            elif c.rejected is True:
                update_identity_from_feedback(identity, c, confirmed=False)
        save_identity(identity)
        if not as_json:
            console.print(f"[green]Updated identity: {identity.display_name}[/green]")

    # Build results
    confirmed = [c for c in candidates if c.confirmed is True]
    rejected = [c for c in candidates if c.rejected is True]
    skipped = [c for c in candidates if c.confirmed is None and c.rejected is None]

    # Output
    if as_json:
        result = {
            "confirmed": [c.model_dump() for c in confirmed],
            "rejected": [c.model_dump() for c in rejected],
            "skipped": [c.model_dump() for c in skipped],
            "count": {"confirmed": len(confirmed), "rejected": len(rejected), "skipped": len(skipped)},
        }
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        console.print(f"\n[green]Confirmed: {len(confirmed)}[/green]")
        console.print(f"[red]Rejected: {len(rejected)}[/red]")
        console.print(f"[dim]Skipped: {len(skipped)}[/dim]")

    # Save confirmed candidates
    if output and confirmed:
        confirmed_set = CandidateSet(
            query=candidate_set.query,
            identity_slug=identity_slug,
            candidates=confirmed,
        )
        with open(output, "w") as f:
            f.write(confirmed_set.model_dump_json(indent=2))
        if not as_json:
            console.print(f"\nSaved {len(confirmed)} confirmed candidates to: {output}")


@main.command()
@click.argument("input", type=click.Path(exists=True), required=False)
@click.option("--identity", "-i", "identity_slug", help="Fetch all confirmed videos from identity")
@click.option("--output-dir", "-o", type=click.Path(), default="./transcripts", help="Output directory")
@click.option("--lang", default="en", help="Preferred language code")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def fetch(
    input: str | None,
    identity_slug: str | None,
    output_dir: str,
    lang: str,
    as_json: bool,
) -> None:
    """Download transcripts for confirmed videos.
    
    INPUT can be a confirmed.json file from 'wve confirm'.
    Alternatively, use --identity to fetch all confirmed videos from an identity.
    """
    from pathlib import Path

    from rich.console import Console
    from rich.progress import Progress

    from wve.classify import CandidateSet
    from wve.identity import load_identity
    from wve.models import VideoMetadata
    from wve.transcripts import download_transcript

    console = Console(stderr=True)

    # Collect video URLs to fetch
    videos_to_fetch: list[tuple[str, str, str]] = []  # (id, url, title)

    if identity_slug:
        try:
            identity = load_identity(identity_slug)
        except FileNotFoundError:
            console.print(f"[red]Identity not found: {identity_slug}[/red]")
            raise SystemExit(1)

        for vid_id in identity.confirmed_videos:
            url = f"https://www.youtube.com/watch?v={vid_id}"
            videos_to_fetch.append((vid_id, url, ""))

        if not as_json:
            console.print(f"Fetching {len(videos_to_fetch)} confirmed videos from {identity.display_name}")

    elif input:
        with open(input) as f:
            candidate_set = CandidateSet.model_validate_json(f.read())

        for c in candidate_set.candidates:
            if c.confirmed:
                videos_to_fetch.append((c.id, c.url, c.title))

        if not as_json:
            console.print(f"Fetching {len(videos_to_fetch)} videos from {input}")

    else:
        console.print("[red]Provide either INPUT file or --identity[/red]")
        raise SystemExit(1)

    if not videos_to_fetch:
        if as_json:
            click.echo(json.dumps({"fetched": 0, "transcripts": []}))
        else:
            console.print("[yellow]No confirmed videos to fetch[/yellow]")
        return

    # Download transcripts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = []
    failed = []

    if as_json:
        for vid_id, url, title in videos_to_fetch:
            transcript_path = download_transcript(url, output_path, lang)
            if transcript_path:
                results.append({"id": vid_id, "path": str(transcript_path)})
            else:
                failed.append(vid_id)
    else:
        with Progress(console=console) as progress:
            task = progress.add_task("Downloading transcripts...", total=len(videos_to_fetch))

            for vid_id, url, title in videos_to_fetch:
                progress.update(task, description=f"[dim]{vid_id}[/dim]")
                transcript_path = download_transcript(url, output_path, lang)
                if transcript_path:
                    results.append({"id": vid_id, "path": str(transcript_path)})
                else:
                    failed.append(vid_id)
                progress.advance(task)

    # Output
    if as_json:
        click.echo(json.dumps({
            "fetched": len(results),
            "failed": len(failed),
            "transcripts": results,
            "output_dir": str(output_path),
        }, indent=2))
    else:
        console.print(f"\n[green]Fetched: {len(results)} transcripts[/green]")
        if failed:
            console.print(f"[red]Failed: {len(failed)}[/red]")
            for vid_id in failed[:5]:
                console.print(f"  [dim]{vid_id}[/dim]")
            if len(failed) > 5:
                console.print(f"  [dim]... and {len(failed) - 5} more[/dim]")
        console.print(f"\nSaved to: {output_path}/")


# === Source Commands (v0.2) ===


@main.command("from-channel")
@click.argument("channel_url")
@click.option("--output-dir", "-o", type=click.Path(), default="./transcripts", help="Output directory")
@click.option("--max-videos", "-n", default=50, help="Maximum videos to fetch")
@click.option("--min-duration", default=5, help="Minimum video length in minutes")
@click.option("--max-duration", default=180, help="Maximum video length in minutes")
@click.option("--after", help="Only videos after date (YYYY-MM-DD)")
@click.option("--before", help="Only videos before date (YYYY-MM-DD)")
@click.option("--lang", default="en", help="Preferred transcript language")
@click.option("--identity", "-i", "identity_slug", help="Add to identity's confirmed videos")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def from_channel(
    channel_url: str,
    output_dir: str,
    max_videos: int,
    min_duration: int,
    max_duration: int,
    after: str | None,
    before: str | None,
    lang: str,
    identity_slug: str | None,
    as_json: bool,
) -> None:
    """Scrape all videos from a YouTube channel.
    
    This is the most reliable way to get content from someone with their own channel.
    All videos are automatically confirmed (no search ambiguity).
    """
    import subprocess
    from datetime import datetime
    from pathlib import Path

    from rich.console import Console
    from rich.progress import Progress

    from wve.identity import add_video_to_identity, load_identity, save_identity
    from wve.transcripts import download_transcript

    console = Console(stderr=True)

    # Parse date filters
    after_date = datetime.strptime(after, "%Y-%m-%d") if after else None
    before_date = datetime.strptime(before, "%Y-%m-%d") if before else None

    # Get channel videos using yt-dlp
    if not as_json:
        console.print(f"Fetching video list from: {channel_url}")

    cmd = [
        "yt-dlp",
        channel_url,
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        f"--playlist-end={max_videos * 2}",  # Fetch extra to filter
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
    except subprocess.TimeoutExpired:
        console.print("[red]Timeout fetching channel videos[/red]")
        raise SystemExit(1)
    except OSError as e:
        console.print(f"[red]yt-dlp not found: {e}[/red]")
        raise SystemExit(1)

    if result.returncode != 0 and not result.stdout.strip():
        console.print(f"[red]Failed to fetch channel: {result.stderr}[/red]")
        raise SystemExit(1)

    # Parse videos
    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        duration = data.get("duration") or 0
        duration_minutes = duration / 60

        # Apply filters
        if duration_minutes < min_duration or duration_minutes > max_duration:
            continue

        # Parse upload date
        upload_date = data.get("upload_date", "")
        published = None
        if upload_date and len(upload_date) == 8:
            published = datetime.strptime(upload_date, "%Y%m%d")
            if after_date and published < after_date:
                continue
            if before_date and published > before_date:
                continue

        vid_id = data.get("id", "")
        videos.append({
            "id": vid_id,
            "title": data.get("title", ""),
            "duration": duration,
            "published": published.isoformat() if published else None,
            "url": data.get("webpage_url", f"https://www.youtube.com/watch?v={vid_id}"),
        })

        if len(videos) >= max_videos:
            break

    if not videos:
        if as_json:
            click.echo(json.dumps({"fetched": 0, "videos": []}))
        else:
            console.print("[yellow]No videos found matching criteria[/yellow]")
        return

    if not as_json:
        console.print(f"Found {len(videos)} videos, downloading transcripts...")

    # Download transcripts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = []
    failed = []

    # Load identity if provided
    identity = None
    if identity_slug:
        try:
            identity = load_identity(identity_slug)
        except FileNotFoundError:
            console.print(f"[red]Identity not found: {identity_slug}[/red]")
            raise SystemExit(1)

    if as_json:
        for video in videos:
            transcript_path = download_transcript(video["url"], output_path, lang)
            if transcript_path:
                results.append({"id": video["id"], "title": video["title"], "path": str(transcript_path)})
                if identity:
                    add_video_to_identity(identity_slug, video["id"], confirmed=True)
            else:
                failed.append(video["id"])
    else:
        with Progress(console=console) as progress:
            task = progress.add_task("Downloading...", total=len(videos))
            for video in videos:
                progress.update(task, description=f"[dim]{video['id']}[/dim]")
                transcript_path = download_transcript(video["url"], output_path, lang)
                if transcript_path:
                    results.append({"id": video["id"], "title": video["title"], "path": str(transcript_path)})
                    if identity:
                        add_video_to_identity(identity_slug, video["id"], confirmed=True)
                else:
                    failed.append(video["id"])
                progress.advance(task)

    # Output
    if as_json:
        click.echo(json.dumps({
            "fetched": len(results),
            "failed": len(failed),
            "transcripts": results,
            "output_dir": str(output_path),
        }, indent=2))
    else:
        console.print(f"\n[green]Fetched: {len(results)} transcripts[/green]")
        if failed:
            console.print(f"[red]Failed: {len(failed)} (no captions)[/red]")
        if identity:
            console.print(f"[green]Added {len(results)} videos to {identity.display_name}[/green]")
        console.print(f"\nSaved to: {output_path}/")


@main.command("from-rss")
@click.argument("feed_url")
@click.option("--output-dir", "-o", type=click.Path(), default="./transcripts", help="Output directory")
@click.option("--max-episodes", "-n", default=20, help="Maximum episodes to fetch")
@click.option("--after", help="Only episodes after date (YYYY-MM-DD)")
@click.option("--identity", "-i", "identity_slug", help="Add to identity's confirmed videos")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def from_rss(
    feed_url: str,
    output_dir: str,
    max_episodes: int,
    after: str | None,
    identity_slug: str | None,
    as_json: bool,
) -> None:
    """Ingest podcast episodes from an RSS feed.
    
    Downloads audio and transcribes using Whisper (requires whisper to be installed).
    Currently supports YouTube RSS feeds directly; for audio podcasts, transcription
    is not yet implemented.
    """
    import subprocess
    import xml.etree.ElementTree as ET
    from datetime import datetime
    from pathlib import Path
    from urllib.request import urlopen

    from rich.console import Console

    console = Console(stderr=True)

    # Parse date filter
    after_date = datetime.strptime(after, "%Y-%m-%d") if after else None

    if not as_json:
        console.print(f"Fetching RSS feed: {feed_url}")

    try:
        with urlopen(feed_url, timeout=30) as response:
            feed_content = response.read()
    except Exception as e:
        console.print(f"[red]Failed to fetch RSS feed: {e}[/red]")
        raise SystemExit(1)

    try:
        root = ET.fromstring(feed_content)
    except ET.ParseError as e:
        console.print(f"[red]Failed to parse RSS feed: {e}[/red]")
        raise SystemExit(1)

    # Find items/entries
    episodes = []
    
    # Try Atom format first
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall(".//atom:entry", ns)
    
    if entries:
        # Atom format (YouTube RSS)
        for entry in entries[:max_episodes * 2]:
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            published_el = entry.find("atom:published", ns)
            
            title = title_el.text if title_el is not None else ""
            link = link_el.get("href", "") if link_el is not None else ""
            
            pub_date = None
            if published_el is not None and published_el.text:
                try:
                    pub_date = datetime.fromisoformat(published_el.text.replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            if after_date and pub_date and pub_date.replace(tzinfo=None) < after_date:
                continue
                
            if link:
                episodes.append({"title": title, "url": link, "published": pub_date})
    else:
        # RSS 2.0 format
        items = root.findall(".//item")
        for item in items[:max_episodes * 2]:
            title_el = item.find("title")
            link_el = item.find("link")
            
            title = title_el.text if title_el is not None else ""
            link = link_el.text if link_el is not None else ""
            
            if link:
                episodes.append({"title": title, "url": link, "published": None})

    episodes = episodes[:max_episodes]

    if not episodes:
        if as_json:
            click.echo(json.dumps({"fetched": 0, "episodes": []}))
        else:
            console.print("[yellow]No episodes found in feed[/yellow]")
        return

    if not as_json:
        console.print(f"Found {len(episodes)} episodes")

    # For YouTube RSS feeds, we can use the existing transcript download
    from wve.identity import add_video_to_identity, extract_video_id, load_identity
    from wve.transcripts import download_transcript

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    identity = None
    if identity_slug:
        try:
            identity = load_identity(identity_slug)
        except FileNotFoundError:
            console.print(f"[red]Identity not found: {identity_slug}[/red]")
            raise SystemExit(1)

    results = []
    failed = []

    for ep in episodes:
        url = ep["url"]
        vid_id = extract_video_id(url)
        
        transcript_path = download_transcript(url, output_path, "en")
        if transcript_path:
            results.append({"id": vid_id, "title": ep["title"], "path": str(transcript_path)})
            if identity:
                add_video_to_identity(identity_slug, vid_id, confirmed=True)
        else:
            failed.append(vid_id)

    if as_json:
        click.echo(json.dumps({
            "fetched": len(results),
            "failed": len(failed),
            "transcripts": results,
        }, indent=2))
    else:
        console.print(f"\n[green]Fetched: {len(results)} transcripts[/green]")
        if failed:
            console.print(f"[red]Failed: {len(failed)} (no captions/not YouTube)[/red]")
        console.print(f"Saved to: {output_path}/")


@main.command("from-urls")
@click.argument("input", type=click.Path(exists=True), required=False)
@click.option("--url", "-u", multiple=True, help="Video URL (can specify multiple)")
@click.option("--output-dir", "-o", type=click.Path(), default="./transcripts", help="Output directory")
@click.option("--lang", default="en", help="Preferred transcript language")
@click.option("--identity", "-i", "identity_slug", help="Add to identity's confirmed videos")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def from_urls(
    input: str | None,
    url: tuple[str, ...],
    output_dir: str,
    lang: str,
    identity_slug: str | None,
    yes: bool,
    as_json: bool,
) -> None:
    """Process manually curated video URLs.
    
    INPUT is a file with one URL per line.
    Alternatively, use --url flags for individual URLs.
    
    This is the most accurate method - user guarantees correctness.
    """
    from pathlib import Path

    from rich.console import Console
    from rich.progress import Progress

    from wve.identity import add_video_to_identity, extract_video_id, load_identity
    from wve.transcripts import download_transcript

    console = Console(stderr=True)

    # Collect URLs
    urls = list(url)
    if input:
        with open(input) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

    if not urls:
        console.print("[red]No URLs provided. Use INPUT file or --url flags.[/red]")
        raise SystemExit(1)

    if not as_json:
        console.print(f"Processing {len(urls)} URLs")

    if not yes and not as_json:
        from rich.prompt import Confirm
        if not Confirm.ask(f"Download transcripts for {len(urls)} videos?"):
            console.print("Cancelled.")
            return

    # Load identity if provided
    identity = None
    if identity_slug:
        try:
            identity = load_identity(identity_slug)
        except FileNotFoundError:
            console.print(f"[red]Identity not found: {identity_slug}[/red]")
            raise SystemExit(1)

    # Download transcripts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = []
    failed = []

    if as_json:
        for video_url in urls:
            vid_id = extract_video_id(video_url)
            transcript_path = download_transcript(video_url, output_path, lang)
            if transcript_path:
                results.append({"id": vid_id, "url": video_url, "path": str(transcript_path)})
                if identity:
                    add_video_to_identity(identity_slug, vid_id, confirmed=True)
            else:
                failed.append(vid_id)
    else:
        with Progress(console=console) as progress:
            task = progress.add_task("Downloading...", total=len(urls))
            for video_url in urls:
                vid_id = extract_video_id(video_url)
                progress.update(task, description=f"[dim]{vid_id}[/dim]")
                transcript_path = download_transcript(video_url, output_path, lang)
                if transcript_path:
                    results.append({"id": vid_id, "url": video_url, "path": str(transcript_path)})
                    if identity:
                        add_video_to_identity(identity_slug, vid_id, confirmed=True)
                else:
                    failed.append(vid_id)
                progress.advance(task)

    # Output
    if as_json:
        click.echo(json.dumps({
            "fetched": len(results),
            "failed": len(failed),
            "transcripts": results,
            "output_dir": str(output_path),
        }, indent=2))
    else:
        console.print(f"\n[green]Fetched: {len(results)} transcripts[/green]")
        if failed:
            console.print(f"[red]Failed: {len(failed)} (no captions)[/red]")
        if identity:
            console.print(f"[green]Added {len(results)} videos to {identity.display_name}[/green]")
        console.print(f"\nSaved to: {output_path}/")


# === Ingestion Commands (v0.3) ===


@main.command()
@click.argument("input", nargs=-1, required=True)
@click.option("--output", "-o", type=click.Path(), default="./sources", help="Output directory for ingested sources")
@click.option("--format", "-f", help="Auto-detect format or specify (youtube, substack, twitter, markdown, pdf, text)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON (for automation)")
def ingest(
    input: tuple[str, ...],
    output: str,
    format: str | None,
    as_json: bool,
) -> None:
    """Ingest content from arbitrary text sources.

    INPUT can be:
    - YouTube video URLs
    - Substack article URLs
    - Twitter/X thread URLs
    - Markdown file paths (.md, .markdown)
    - PDF file paths (.pdf)
    - Plain text file paths
    - Raw text directly

    Examples:
        wve ingest https://youtube.com/watch?v=... -o sources/
        wve ingest https://substack.com/p/... -o sources/
        wve ingest ./blog.md ./book.pdf -o sources/
        wve ingest "Any raw text content here" -o sources/
    """
    from rich.console import Console
    from wve.ingest import ingest_auto, ingest_batch

    console = Console(stderr=True)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not as_json:
        console.print(f"Ingesting {len(input)} source(s)...")

    # Ingest all inputs
    sources = ingest_batch(list(input), output_dir)

    if not sources:
        if not as_json:
            console.print("[yellow]No content ingested from inputs[/yellow]")
        raise SystemExit(1)

    if as_json:
        sources_json = [s.model_dump() for s in sources.values()]
        click.echo(json.dumps(sources_json, indent=2, default=str))
    else:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold")
        table.add_column("Source ID", width=25)
        table.add_column("Type", width=10)
        table.add_column("Format", width=12)
        table.add_column("Characters", width=12)

        for source in sorted(sources.values(), key=lambda s: s.ingested_at):
            table.add_row(
                source.source_id,
                source.source_type,
                source.raw_format,
                f"{len(source.text):,}",
            )

        console.print(table)
        console.print(f"\n[green]Ingested {len(sources)} source(s)[/green]")
        console.print(f"Saved to: {output_dir}/")


# === Analysis Commands (v0.2) ===


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--max-quotes", "-n", default=50, help="Maximum quotes to extract")
@click.option("--min-score", default=0.3, help="Minimum score threshold (0-1)")
@click.option("--contrarian", is_flag=True, help="Prioritize contrarian statements")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def quotes(
    input: str,
    max_quotes: int,
    min_score: float,
    contrarian: bool,
    output: str | None,
    as_json: bool,
) -> None:
    """Extract notable quotes from transcripts.
    
    INPUT is a directory containing transcript .txt files.
    """
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    from wve.quotes import extract_quotes_from_dir

    console = Console(stderr=True)
    input_path = Path(input)

    if not input_path.is_dir():
        console.print("[red]INPUT must be a directory of transcript files[/red]")
        raise SystemExit(1)

    if not as_json:
        console.print(f"Extracting quotes from: {input}")

    collection = extract_quotes_from_dir(
        input_path,
        max_quotes=max_quotes,
        min_score=min_score,
    )

    # Filter contrarian if requested
    if contrarian:
        collection.quotes = [q for q in collection.quotes if q.is_contrarian]
        collection.quotes = collection.quotes[:max_quotes]

    if as_json:
        click.echo(collection.model_dump_json(indent=2))
    else:
        console.print(f"\nFound {len(collection.quotes)} notable quotes from {collection.source_count} sources\n")

        for i, q in enumerate(collection.quotes[:20], 1):
            console.print(f"[bold][{i}][/bold] [dim]({q.source_id})[/dim]")
            console.print(f"  \"{q.text}\"")
            if q.is_contrarian:
                console.print("  [yellow]^ contrarian[/yellow]")
            console.print()

        if len(collection.quotes) > 20:
            console.print(f"[dim]... and {len(collection.quotes) - 20} more quotes[/dim]")

    if output:
        with open(output, "w") as f:
            f.write(collection.model_dump_json(indent=2))
        if not as_json:
            console.print(f"\nSaved to: {output}")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--subject", "-s", help="Subject name for context")
@click.option("--max-themes", "-n", default=10, help="Maximum themes to extract")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def themes(
    input: str,
    subject: str | None,
    max_themes: int,
    output: str | None,
    as_json: bool,
) -> None:
    """Extract themes with supporting quotes from transcripts.
    
    INPUT is a directory containing transcript .txt files.
    Unlike simple keyword extraction, this grounds each theme in actual quotes.
    """
    from pathlib import Path

    from rich.console import Console

    from wve.quotes import extract_quotes_from_dir

    console = Console(stderr=True)
    input_path = Path(input)

    if not input_path.is_dir():
        console.print("[red]INPUT must be a directory of transcript files[/red]")
        raise SystemExit(1)

    if not as_json:
        console.print(f"Extracting themes from: {input}")

    # First extract quotes
    collection = extract_quotes_from_dir(input_path, max_quotes=100, min_score=0.2)

    # Simple theme grouping by common words/phrases
    # This is a basic implementation - could be enhanced with clustering
    from collections import Counter

    word_counts: Counter[str] = Counter()
    for quote in collection.quotes:
        words = quote.text.lower().split()
        # Skip common words
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "shall", "can", "to", "of", "in",
                     "for", "on", "with", "at", "by", "from", "as", "or", "and", "but",
                     "if", "then", "so", "than", "that", "this", "these", "those", "it",
                     "its", "you", "your", "i", "my", "me", "we", "our", "they", "their"}
        meaningful = [w for w in words if len(w) > 3 and w not in stopwords]
        word_counts.update(meaningful)

    # Build themes from top words
    themes_data = []
    used_quotes = set()

    for word, count in word_counts.most_common(max_themes * 2):
        if len(themes_data) >= max_themes:
            break

        # Find quotes containing this word
        supporting = []
        for q in collection.quotes:
            if q.text in used_quotes:
                continue
            if word in q.text.lower():
                supporting.append(q)
                used_quotes.add(q.text)
                if len(supporting) >= 3:
                    break

        if supporting:
            themes_data.append({
                "name": word.title(),
                "frequency": count,
                "supporting_quotes": [{"text": q.text, "source": q.source_id} for q in supporting],
            })

    result = {
        "subject": subject,
        "themes": themes_data,
        "source_count": collection.source_count,
    }

    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        console.print(f"\nFound {len(themes_data)} themes from {collection.source_count} sources\n")

        for theme in themes_data:
            console.print(f"[bold]{theme['name']}[/bold] (mentioned {theme['frequency']}x)")
            for sq in theme["supporting_quotes"][:2]:
                console.print(f"  [dim]\"{sq['text'][:80]}...\"[/dim]")
            console.print()

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        if not as_json:
            console.print(f"Saved to: {output}")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--subject", "-s", required=True, help="Subject name")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def contrast(
    input: str,
    subject: str,
    output: str | None,
    as_json: bool,
) -> None:
    """Find contrarian or distinctive beliefs from transcripts.
    
    INPUT is a directory containing transcript .txt files.
    Extracts quotes that suggest non-mainstream or counterintuitive views.
    """
    from pathlib import Path

    from rich.console import Console

    from wve.quotes import extract_quotes_from_dir

    console = Console(stderr=True)
    input_path = Path(input)

    if not input_path.is_dir():
        console.print("[red]INPUT must be a directory of transcript files[/red]")
        raise SystemExit(1)

    if not as_json:
        console.print(f"Finding contrarian views for: {subject}")

    # Extract quotes with lower threshold to catch more contrarian statements
    collection = extract_quotes_from_dir(input_path, max_quotes=200, min_score=0.2)

    # Filter to contrarian quotes
    contrarian_quotes = [q for q in collection.quotes if q.is_contrarian]

    result = {
        "subject": subject,
        "contrarian_count": len(contrarian_quotes),
        "quotes": [q.model_dump() for q in contrarian_quotes[:30]],
        "source_count": collection.source_count,
    }

    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        console.print(f"\nFound {len(contrarian_quotes)} contrarian statements\n")

        for i, q in enumerate(contrarian_quotes[:15], 1):
            console.print(f"[bold][{i}][/bold] [dim]({q.source_id})[/dim]")
            console.print(f"  \"{q.text}\"")
            console.print()

        if len(contrarian_quotes) > 15:
            console.print(f"[dim]... and {len(contrarian_quotes) - 15} more[/dim]")

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        if not as_json:
            console.print(f"\nSaved to: {output}")


@main.command()
@click.argument("identity_slug")
@click.option("--output", "-o", type=click.Path(), help="Save new candidates to JSON")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def refine(
    identity_slug: str,
    output: str | None,
    as_json: bool,
) -> None:
    """Interactive search refinement to find more content for an identity.
    
    Suggests additional searches based on confirmed videos and channel patterns.
    """
    from rich.console import Console
    from rich.prompt import Prompt

    from wve.classify import CandidateSet, VideoCandidate, classify_candidates
    from wve.identity import load_identity
    from wve.search import search_videos

    console = Console(stderr=True)

    try:
        identity = load_identity(identity_slug)
    except FileNotFoundError:
        console.print(f"[red]Identity not found: {identity_slug}[/red]")
        raise SystemExit(1)

    # Generate search suggestions based on identity
    suggestions = [
        f'"{identity.display_name}" interview',
        f'"{identity.display_name}" podcast',
        f'"{identity.display_name}" talk',
    ]
    
    for alias in identity.aliases[:2]:
        suggestions.append(f'"{alias}" interview')

    # Stats
    confirmed_count = len(identity.confirmed_videos)
    channel_count = len(identity.channels)

    if as_json:
        result = {
            "identity": identity_slug,
            "display_name": identity.display_name,
            "confirmed_videos": confirmed_count,
            "channels": channel_count,
            "suggested_searches": suggestions,
        }
        click.echo(json.dumps(result, indent=2))
        return

    console.print(f"\n[bold]Refining: {identity.display_name}[/bold]")
    console.print(f"Current corpus: {confirmed_count} confirmed videos, {channel_count} channel(s)\n")

    console.print("[bold]Suggested searches:[/bold]")
    for i, s in enumerate(suggestions, 1):
        console.print(f"  [{i}] {s}")
    console.print()

    choice = Prompt.ask(
        "Enter number to search, custom query, or 'q' to quit",
        default="q"
    )

    if choice.lower() == "q":
        console.print("Done.")
        return

    # Determine search query
    if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
        query = suggestions[int(choice) - 1]
    else:
        query = choice

    console.print(f"\nSearching: {query}")
    results = search_videos(query, max_results=20)

    # Convert and classify
    candidates = [
        VideoCandidate(
            id=v.id,
            title=v.title,
            channel=v.channel,
            channel_id=v.channel_id,
            duration_seconds=v.duration_seconds,
            url=v.url,
            published=v.published,
        )
        for v in results.videos
    ]

    # Filter out already confirmed/rejected
    new_candidates = [
        c for c in candidates
        if c.id not in identity.confirmed_videos and c.id not in identity.rejected_videos
    ]

    classify_candidates(new_candidates, identity.display_name, identity)

    console.print(f"\nFound {len(new_candidates)} new candidates")

    # Group by classification
    likely = [c for c in new_candidates if c.classification == "likely"]
    uncertain = [c for c in new_candidates if c.classification == "uncertain"]

    if likely:
        console.print(f"\n[green]Likely matches: {len(likely)}[/green]")
        for c in likely[:5]:
            console.print(f"  - {c.title[:60]}")

    if uncertain:
        console.print(f"\n[yellow]Uncertain: {len(uncertain)}[/yellow]")

    if output and new_candidates:
        candidate_set = CandidateSet(
            query=query,
            identity_slug=identity_slug,
            candidates=new_candidates,
        )
        with open(output, "w") as f:
            f.write(candidate_set.model_dump_json(indent=2))
        console.print(f"\nSaved to: {output}")


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--subject", "-s", required=True, help="Subject name")
@click.option("--output", "-o", type=click.Path(), help="Output markdown file")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON instead of markdown")
def report(
    input: str,
    subject: str,
    output: str | None,
    as_json: bool,
) -> None:
    """Generate comprehensive worldview report from transcripts.
    
    INPUT is a directory containing transcript .txt files.
    Produces a markdown report with themes, quotes, and contrarian beliefs.
    """
    from datetime import datetime
    from pathlib import Path

    from rich.console import Console

    from wve.quotes import extract_quotes_from_dir

    console = Console(stderr=True)
    input_path = Path(input)

    if not input_path.is_dir():
        console.print("[red]INPUT must be a directory of transcript files[/red]")
        raise SystemExit(1)

    if not as_json:
        console.print(f"Generating report for: {subject}")

    # Extract quotes
    collection = extract_quotes_from_dir(input_path, max_quotes=100, min_score=0.2)

    # Separate contrarian quotes
    contrarian = [q for q in collection.quotes if q.is_contrarian]
    top_quotes = collection.quotes[:20]

    # Extract themes (simple word frequency)
    from collections import Counter
    word_counts: Counter[str] = Counter()
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                 "have", "has", "had", "do", "does", "did", "will", "would", "could",
                 "should", "may", "might", "must", "shall", "can", "to", "of", "in",
                 "for", "on", "with", "at", "by", "from", "as", "or", "and", "but",
                 "if", "then", "so", "than", "that", "this", "these", "those", "it",
                 "its", "you", "your", "i", "my", "me", "we", "our", "they", "their"}
    
    for quote in collection.quotes:
        words = quote.text.lower().split()
        meaningful = [w for w in words if len(w) > 3 and w not in stopwords]
        word_counts.update(meaningful)

    top_themes = word_counts.most_common(10)

    if as_json:
        result = {
            "subject": subject,
            "generated_at": datetime.now().isoformat(),
            "source_count": collection.source_count,
            "total_quotes": len(collection.quotes),
            "themes": [{"name": w, "count": c} for w, c in top_themes],
            "top_quotes": [q.model_dump() for q in top_quotes],
            "contrarian_quotes": [q.model_dump() for q in contrarian[:15]],
        }
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        # Generate markdown report
        lines = [
            f"# Worldview Report: {subject}",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            "---",
            "",
            "## Overview",
            "",
            f"- **Sources analyzed:** {collection.source_count} transcripts",
            f"- **Notable quotes extracted:** {len(collection.quotes)}",
            f"- **Contrarian statements:** {len(contrarian)}",
            "",
            "---",
            "",
            "## Key Themes",
            "",
        ]

        for word, count in top_themes:
            lines.append(f"- **{word.title()}** (mentioned {count}x)")
        
        lines.extend([
            "",
            "---",
            "",
            "## Notable Quotes",
            "",
        ])

        for i, q in enumerate(top_quotes[:15], 1):
            lines.append(f"{i}. \"{q.text}\"")
            lines.append(f"   *— {q.source_id}*")
            lines.append("")

        if contrarian:
            lines.extend([
                "---",
                "",
                "## Contrarian / Distinctive Views",
                "",
                "These statements suggest views that differ from mainstream thinking:",
                "",
            ])

            for i, q in enumerate(contrarian[:10], 1):
                lines.append(f"{i}. \"{q.text}\"")
                lines.append(f"   *— {q.source_id}*")
                lines.append("")

        lines.extend([
            "---",
            "",
            "*Report generated by wve (Worldview Extractor) v0.2*",
        ])

        report_text = "\n".join(lines)

        if output:
            Path(output).write_text(report_text)
            console.print(f"Report saved to: {output}")
        else:
            click.echo(report_text)


# === Legacy v0.1 Commands ===


@main.command()
@click.argument("person")
@click.option("--max-results", "-n", default=10, help="Maximum videos to find")
@click.option("--channel", help="Limit to specific channel URL")
@click.option("--min-duration", default=5, help="Minimum video length in minutes")
@click.option("--max-duration", default=180, help="Maximum video length in minutes")
@click.option("--output", "-o", type=click.Path(), help="Save results to JSON file")
@click.option("--strict", is_flag=True, help="Only include videos with query in title")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON (for automation)")
def search(
    person: str,
    max_results: int,
    channel: str | None,
    min_duration: int,
    max_duration: int,
    output: str | None,
    strict: bool,
    as_json: bool,
) -> None:
    """Discover videos featuring PERSON."""
    from wve.search import save_search_results, search_videos

    if not as_json:
        click.echo(f"Searching for videos featuring: {person}", err=True)
    results = search_videos(
        person,
        max_results=max_results,
        min_duration=min_duration,
        max_duration=max_duration,
        channel=channel,
    )

    if strict:
        query_lower = person.lower()
        results.videos = [v for v in results.videos if query_lower in v.title.lower()]

    if as_json:
        click.echo(results.model_dump_json(indent=2))
    elif output:
        save_search_results(results, output)
        click.echo(f"Found {len(results.videos)} videos, saved to {output}", err=True)
    else:
        click.echo(f"Found {len(results.videos)} videos", err=True)
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
@click.option("--extraction", "-e", "extraction_path", type=click.Path(exists=True), help="Extraction JSON (required for medium/deep if INPUT is clusters)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON (for automation)")
def synthesize(input: str, depth: str, points: int, model: str, output: str | None, subject: str, extraction_path: str | None, as_json: bool) -> None:
    """Synthesize worldview points from extracted/clustered data."""
    from wve.cluster import load_clusters
    from wve.models import Extraction
    from wve.synthesize import save_worldview
    from wve.synthesize import synthesize as do_synthesize

    input_path = Path(input)
    with open(input_path) as f:
        data = json.load(f)

    if "clusters" in data:
        clusters = load_clusters(input)
        # Load extraction from sibling file or explicit path
        extraction = None
        if extraction_path:
            with open(extraction_path) as ef:
                extraction = Extraction.model_validate_json(ef.read())
        elif depth in ("medium", "deep"):
            # Try to find extraction.json in same directory
            sibling = input_path.parent / "extraction.json"
            if sibling.exists():
                with open(sibling) as ef:
                    extraction = Extraction.model_validate_json(ef.read())
                if not as_json:
                    click.echo(f"Auto-loaded extraction from {sibling}", err=True)
    else:
        extraction = Extraction.model_validate(data)
        from wve.cluster import cluster_extraction

        clusters = cluster_extraction(extraction)

    if not as_json:
        click.echo(f"Synthesizing at depth: {depth}", err=True)
    worldview = do_synthesize(clusters, extraction, subject=subject, depth=depth, n_points=points, model=model)

    if as_json:
        click.echo(worldview.model_dump_json(indent=2))
    else:
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


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--format", "fmt", type=click.Choice(["plain", "markdown"]), default="markdown", help="Output format")
@click.option("--max-tokens", default=0, help="Warn if estimated tokens exceed this (0=no limit)")
def dump(input: str, output: str | None, fmt: str, max_tokens: int) -> None:
    """Concatenate transcripts for direct LLM use."""
    from wve.rag import load_transcripts_for_rag

    input_path = Path(input)
    transcripts, titles = load_transcripts_for_rag(input_path)

    if not transcripts:
        click.echo("No transcripts found.", err=True)
        return

    parts = []
    for vid, text in transcripts.items():
        title = titles.get(vid, vid)
        if fmt == "markdown":
            parts.append(f"## {title}\n\n{text}")
        else:
            parts.append(f"=== {title} ===\n\n{text}")

    separator = "\n\n---\n\n" if fmt == "markdown" else "\n\n"
    result = separator.join(parts)

    estimated_tokens = len(result) // 4
    click.echo(f"Transcripts: {len(transcripts)}, ~{estimated_tokens:,} tokens", err=True)

    if max_tokens > 0 and estimated_tokens > max_tokens:
        click.echo(f"WARNING: Exceeds --max-tokens {max_tokens:,}", err=True)

    if output:
        Path(output).write_text(result)
        click.echo(f"Saved to {output}", err=True)
    else:
        click.echo(result)


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.argument("question")
@click.option("--top-k", "-k", default=5, help="Number of chunks to retrieve")
@click.option("--model", default="mistral", help="Ollama model for answering")
@click.option("--show-sources", is_flag=True, help="Show source chunks")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON (for automation)")
def ask(input: str, question: str, top_k: int, model: str, show_sources: bool, as_json: bool) -> None:
    """Ask a question about the transcript corpus."""
    from wve.rag import ask_corpus, build_index, chunk_transcripts, load_transcripts_for_rag, search_index

    input_path = Path(input)
    transcripts, titles = load_transcripts_for_rag(input_path)

    if not transcripts:
        click.echo("No transcripts found.", err=True)
        return

    if not as_json:
        click.echo(f"Building index from {len(transcripts)} transcripts...", err=True)
    chunks = chunk_transcripts(transcripts, titles)
    index = build_index(chunks)

    if show_sources and not as_json:
        results = search_index(index, question, top_k)
        click.echo("\n--- Relevant excerpts ---\n")
        for r in results:
            click.echo(f"[{r.chunk.source_title}] (score: {r.score:.3f})")
            click.echo(r.chunk.text[:500] + "..." if len(r.chunk.text) > 500 else r.chunk.text)
            click.echo()

    if not as_json:
        click.echo("Generating answer...", err=True)
    result = ask_corpus(index, question, top_k=top_k, model=model)

    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"\n{result['answer']}")
        click.echo(f"\n[Sources: {', '.join(result['sources'])}]", err=True)


# === Store Commands ===


@main.group()
def store() -> None:
    """Manage persistent worldview storage (beats-like)."""
    pass


@store.command("save")
@click.argument("input", type=click.Path(exists=True))
@click.option("--name", "-n", required=True, help="Display name for the subject")
@click.option("--slug", "-s", help="Custom slug (default: derived from name)")
@click.option("--channel", "-c", help="YouTube channel URL")
@click.option("--tag", "-t", multiple=True, help="Tags for organization")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def store_save(
    input: str,
    name: str,
    slug: str | None,
    channel: str | None,
    tag: tuple[str, ...],
    as_json: bool,
) -> None:
    """Save a worldview extraction to persistent storage.
    
    INPUT is a directory containing transcript files (the output of from-channel/from-urls).
    """
    from pathlib import Path
    import shutil
    from rich.console import Console
    from wve.identity import slugify
    from wve.store import WorldviewEntry, get_entry_dir, save_entry
    from wve.quotes import extract_quotes_from_dir

    console = Console(stderr=True)
    input_path = Path(input)
    
    if not input_path.is_dir():
        console.print("[red]INPUT must be a directory of transcript files[/red]")
        raise SystemExit(1)
    
    slug = slug or slugify(name)
    
    if not as_json:
        console.print(f"Analyzing transcripts for: {name}")
    
    # Extract quotes and themes
    collection = extract_quotes_from_dir(input_path, max_quotes=100, min_score=0.2)
    
    # Build themes from word frequency
    from collections import Counter
    word_counts: Counter[str] = Counter()
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                 "have", "has", "had", "do", "does", "did", "will", "would", "could",
                 "should", "may", "might", "must", "shall", "can", "to", "of", "in",
                 "for", "on", "with", "at", "by", "from", "as", "or", "and", "but",
                 "if", "then", "so", "than", "that", "this", "these", "those", "it",
                 "its", "you", "your", "i", "my", "me", "we", "our", "they", "their"}
    
    for quote in collection.quotes:
        words = quote.text.lower().split()
        meaningful = [w for w in words if len(w) > 3 and w not in stopwords]
        word_counts.update(meaningful)
    
    themes = [{"name": w.title(), "count": c} for w, c in word_counts.most_common(15)]
    
    # Separate contrarian quotes
    contrarian = [q for q in collection.quotes if q.is_contrarian]
    
    # Create entry
    entry = WorldviewEntry(
        slug=slug,
        display_name=name,
        channel_url=channel,
        source_count=collection.source_count,
        quote_count=len(collection.quotes),
        themes=themes,
        top_quotes=[q.model_dump() for q in collection.quotes[:20]],
        contrarian_quotes=[q.model_dump() for q in contrarian[:15]],
        tags=list(tag),
    )
    
    # Copy transcripts to store
    entry_dir = get_entry_dir(slug)
    transcripts_dest = entry_dir / "transcripts"
    if transcripts_dest.exists():
        shutil.rmtree(transcripts_dest)
    shutil.copytree(input_path, transcripts_dest)
    entry.transcripts_dir = str(transcripts_dest)
    
    # Generate and save report
    from datetime import datetime
    report_lines = [
        f"# Worldview: {name}",
        "",
        f"*Stored: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"- **Sources:** {collection.source_count}",
        f"- **Quotes:** {len(collection.quotes)}",
        f"- **Tags:** {', '.join(tag) if tag else 'none'}",
        "",
        "## Themes",
        "",
    ]
    for t in themes[:10]:
        report_lines.append(f"- **{t['name']}** ({t['count']}x)")
    
    report_lines.extend(["", "## Top Quotes", ""])
    for i, q in enumerate(collection.quotes[:10], 1):
        report_lines.append(f'{i}. "{q.text}"')
        report_lines.append(f"   *— {q.source_id}*")
        report_lines.append("")
    
    if contrarian:
        report_lines.extend(["## Contrarian Views", ""])
        for i, q in enumerate(contrarian[:5], 1):
            report_lines.append(f'{i}. "{q.text}"')
            report_lines.append("")
    
    report_path = entry_dir / "report.md"
    report_path.write_text("\n".join(report_lines))
    entry.report_path = str(report_path)
    
    # Save entry
    save_entry(entry)
    
    if as_json:
        click.echo(entry.model_dump_json(indent=2))
    else:
        console.print(f"\n[green]Saved: {slug}[/green]")
        console.print(f"  Sources: {collection.source_count}")
        console.print(f"  Quotes: {len(collection.quotes)}")
        console.print(f"  Location: {entry_dir}")


@store.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def store_list(as_json: bool) -> None:
    """List all stored worldview extractions."""
    from rich.console import Console
    from rich.table import Table
    from wve.store import list_entries

    console = Console(stderr=True)
    entries = list_entries()
    
    if as_json:
        click.echo(json.dumps([e.model_dump() for e in entries], indent=2, default=str))
    elif not entries:
        console.print("No stored worldviews. Use 'wve store save' to add one.")
    else:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Slug", width=25)
        table.add_column("Name", width=30)
        table.add_column("Sources", width=8)
        table.add_column("Tags", width=20)
        table.add_column("Updated", width=12)
        
        for e in entries:
            tags = ", ".join(e.tags[:3]) if e.tags else ""
            updated = e.updated_at.strftime("%Y-%m-%d") if e.updated_at else ""
            table.add_row(e.slug, e.display_name, str(e.source_count), tags, updated)
        
        console.print(table)


@store.command("show")
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def store_show(slug: str, as_json: bool) -> None:
    """Show details for a stored worldview."""
    from rich.console import Console
    from wve.store import load_entry

    console = Console(stderr=True)
    
    try:
        entry = load_entry(slug)
    except FileNotFoundError:
        console.print(f"[red]Not found: {slug}[/red]")
        raise SystemExit(1)
    
    if as_json:
        click.echo(entry.model_dump_json(indent=2))
    else:
        console.print(f"\n[bold]{entry.display_name}[/bold] ({entry.slug})")
        console.print(f"  Sources: {entry.source_count}")
        console.print(f"  Quotes: {entry.quote_count}")
        if entry.channel_url:
            console.print(f"  Channel: {entry.channel_url}")
        if entry.tags:
            console.print(f"  Tags: {', '.join(entry.tags)}")
        console.print(f"  Updated: {entry.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        if entry.themes:
            console.print("\n[bold]Top Themes:[/bold]")
            for t in entry.themes[:5]:
                console.print(f"  - {t['name']} ({t['count']}x)")
        
        if entry.top_quotes:
            console.print("\n[bold]Sample Quotes:[/bold]")
            for q in entry.top_quotes[:3]:
                console.print(f'  "{q["text"][:80]}..."')


@store.command("search")
@click.argument("query")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def store_search(query: str, as_json: bool) -> None:
    """Search stored worldviews by name, slug, or tags."""
    from rich.console import Console
    from wve.store import search_entries

    console = Console(stderr=True)
    results = search_entries(query)
    
    if as_json:
        click.echo(json.dumps([e.model_dump() for e in results], indent=2, default=str))
    elif not results:
        console.print(f"No matches for: {query}")
    else:
        console.print(f"Found {len(results)} match(es):\n")
        for e in results:
            console.print(f"  [bold]{e.slug}[/bold] - {e.display_name} ({e.source_count} sources)")


@store.command("delete")
@click.argument("slug")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def store_delete(slug: str, yes: bool) -> None:
    """Delete a stored worldview."""
    from rich.console import Console
    from rich.prompt import Confirm
    from wve.store import delete_entry, load_entry

    console = Console(stderr=True)
    
    try:
        entry = load_entry(slug)
    except FileNotFoundError:
        console.print(f"[red]Not found: {slug}[/red]")
        raise SystemExit(1)
    
    if not yes:
        if not Confirm.ask(f"Delete '{entry.display_name}'?"):
            console.print("Cancelled.")
            return
    
    delete_entry(slug)
    console.print(f"[green]Deleted: {slug}[/green]")


if __name__ == "__main__":
    main()
