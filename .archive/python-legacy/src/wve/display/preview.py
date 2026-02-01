"""Video preview formatting for candidate selection."""


def format_video_preview(metadata: dict) -> str:
    """Format video metadata for preview pane.
    
    Shows: channel, date, duration, views, description snippet.
    Returns Rich markup string for TUI display.
    """
    if not metadata:
        return "[dim]No metadata available[/dim]"
    
    lines = []
    
    # Channel
    channel = metadata.get("channel") or metadata.get("uploader") or metadata.get("channel_name")
    if channel:
        lines.append(f"[dim]Channel:[/dim] {channel}")
    
    # Published date
    date = metadata.get("upload_date") or metadata.get("published") or metadata.get("date")
    if date:
        if len(date) == 8 and date.isdigit():
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        lines.append(f"[dim]Published:[/dim] {date}")
    
    # Duration
    duration = metadata.get("duration") or metadata.get("duration_string")
    if duration:
        if isinstance(duration, (int, float)):
            mins = int(duration) // 60
            secs = int(duration) % 60
            if mins >= 60:
                hours = mins // 60
                mins = mins % 60
                duration_str = f"{hours}h {mins}m"
            else:
                duration_str = f"{mins}m {secs}s" if secs else f"{mins} minutes"
        else:
            duration_str = str(duration)
        lines.append(f"[dim]Duration:[/dim] {duration_str}")
    
    # Views
    views = metadata.get("view_count") or metadata.get("views")
    if views:
        if isinstance(views, (int, float)):
            if views >= 1_000_000:
                views_str = f"{views / 1_000_000:.1f}M"
            elif views >= 1_000:
                views_str = f"{views / 1_000:.1f}K"
            else:
                views_str = str(int(views))
        else:
            views_str = str(views)
        lines.append(f"[dim]Views:[/dim] {views_str}")
    
    # Separator before description
    if lines:
        lines.append("")
    
    # Description
    description = metadata.get("description") or metadata.get("summary")
    if description:
        lines.append("[dim]Description:[/dim]")
        desc_lines = description.split("\n")
        snippet = []
        char_count = 0
        for line in desc_lines:
            if char_count + len(line) > 300:
                remaining = 300 - char_count
                if remaining > 20:
                    snippet.append(line[:remaining] + "...")
                break
            snippet.append(line)
            char_count += len(line)
            if len(snippet) >= 6:
                break
        lines.extend(snippet)
    
    return "\n".join(lines) if lines else "[dim]No metadata available[/dim]"


def format_preview_header(title: str, max_width: int = 40) -> str:
    """Format preview pane header.
    
    Returns Rich markup string.
    """
    if len(title) > max_width - 4:
        title = title[:max_width - 7] + "..."
    return f"[bold]{title}[/bold]"
