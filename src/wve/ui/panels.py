from rich.panel import Panel
from rich.text import Text

def completion_panel(
    title: str,
    stats: dict[str, str | int],
    next_steps: list[tuple[str, str]] | None = None,
    style: str = "green",
) -> Panel:
    """Create a consistent completion panel."""
    lines = []
    
    for key, value in stats.items():
        lines.append(f"[bold]{key}:[/bold] {value}")
    
    if next_steps:
        lines.append("")
        lines.append("[bold]What's next?[/bold]")
        for cmd, desc in next_steps:
            lines.append(f"  [cyan]{cmd}[/cyan]")
            if desc:
                lines.append(f"      [dim]{desc}[/dim]")
    
    return Panel(
        "\n".join(lines),
        title=f"[{style}]✓ {title}[/{style}]",
        border_style=style,
    )

def error_panel(title: str, message: str, suggestions: list[str] | None = None) -> Panel:
    """Create a consistent error panel."""
    lines = [message]
    
    if suggestions:
        lines.append("")
        lines.append("[bold]Suggestions:[/bold]")
        for s in suggestions:
            lines.append(f"  • {s}")
    
    return Panel(
        "\n".join(lines),
        title=f"[red]✗ {title}[/red]",
        border_style="red",
    )

def info_panel(title: str, content: str, style: str = "cyan") -> Panel:
    """Create a simple info panel."""
    return Panel(content, title=title, border_style=style)
