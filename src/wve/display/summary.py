"""Worldview summary display functions.

Clean typography without boxes - uses bold, dim, unicode separators.
Works both in TUI (returning markup) and CLI (printing directly).
"""

from rich.console import Console

from wve.theme import get_console


def show_extraction_complete(worldview: dict, console: Console | None = None) -> None:
    """Show summary after extraction completes.
    
    Prints directly to console.
    """
    if console is None:
        console = get_console()
    
    slug = worldview.get("slug", "unknown")
    name = worldview.get("name", slug)
    transcript_count = worldview.get("transcript_count", 0)
    quote_count = worldview.get("quote_count", 0)
    themes = worldview.get("themes", [])
    theme_count = len(themes)
    
    console.print(f"[green]✓[/green] [bold]Worldview saved:[/bold] {slug}")
    
    stats_parts = []
    if transcript_count:
        stats_parts.append(f"{transcript_count} transcripts")
    if quote_count:
        stats_parts.append(f"{quote_count} quotes")
    if theme_count:
        stats_parts.append(f"{theme_count} themes")
    
    if stats_parts:
        console.print(f"  [dim]{' · '.join(stats_parts)}[/dim]")
    
    if themes:
        top_themes = themes[:3]
        console.print(f"  [dim]Top themes:[/dim] {', '.join(top_themes)}")
    
    console.print(f"  [dim]Next:[/dim] wve ask {slug} \"...\"")


def show_worldview_detail(entry: dict) -> str:
    """Return formatted detail view for browser.
    
    Returns Rich markup string for TUI display.
    """
    slug = entry.get("slug", "unknown")
    name = entry.get("name", slug)
    transcript_count = entry.get("transcript_count", 0)
    quote_count = entry.get("quote_count", 0)
    themes = entry.get("themes", [])
    
    lines = []
    
    # Header
    if name != slug:
        lines.append(f"[bold]{slug}[/bold] · {name}")
    else:
        lines.append(f"[bold]{slug}[/bold]")
    
    # Separator
    lines.append("[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
    
    # Stats
    if transcript_count:
        lines.append(f"[dim]Sources:[/dim] {transcript_count} transcripts")
    if quote_count:
        lines.append(f"[dim]Quotes:[/dim] {quote_count} notable")
    if themes:
        theme_display = ", ".join(themes[:5])
        if len(themes) > 5:
            theme_display += "..."
        lines.append(f"[dim]Themes:[/dim] {theme_display}")
    
    return "\n".join(lines)


def show_top_quotes(quotes: list, limit: int = 3) -> str:
    """Format top quotes for display.
    
    Returns Rich markup string.
    """
    if not quotes:
        return "[dim]No quotes available[/dim]"
    
    lines = []
    for i, quote in enumerate(quotes[:limit]):
        if isinstance(quote, dict):
            text = quote.get("text", quote.get("quote", str(quote)))
            source = quote.get("source", "")
        else:
            text = str(quote)
            source = ""
        
        # Truncate long quotes
        if len(text) > 120:
            text = text[:117] + "..."
        
        lines.append(f"[italic]\"{text}\"[/italic]")
        if source:
            lines.append(f"  [dim]— {source}[/dim]")
        
        if i < min(limit, len(quotes)) - 1:
            lines.append("")
    
    return "\n".join(lines)


def show_worldview_list(worldviews: list) -> str:
    """Format list of worldviews for display.
    
    Returns Rich markup string.
    """
    if not worldviews:
        return "[dim]No worldviews found[/dim]"
    
    lines = []
    for wv in worldviews:
        slug = wv.get("slug", "unknown")
        name = wv.get("name", "")
        quote_count = wv.get("quote_count", 0)
        
        if name and name != slug:
            lines.append(f"• [bold]{slug}[/bold] · {name}")
        else:
            lines.append(f"• [bold]{slug}[/bold]")
        
        if quote_count:
            lines.append(f"  [dim]{quote_count} quotes[/dim]")
    
    return "\n".join(lines)


def format_stats_line(stats: dict) -> str:
    """Format a stats dict as a single line.
    
    Returns Rich markup string like: "12 transcripts · 47 quotes · 8 themes"
    """
    parts = []
    for key, value in stats.items():
        if value:
            parts.append(f"{value} {key}")
    
    return "[dim]" + " · ".join(parts) + "[/dim]" if parts else ""
