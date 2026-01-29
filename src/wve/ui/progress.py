"""Multi-stage progress tracking for wve operations."""

from dataclasses import dataclass, field
from typing import Literal

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.table import Table
from rich.text import Text


ItemStatus = Literal["pending", "active", "done", "failed", "skipped"]


@dataclass
class StageProgress:
    """Track multi-stage operations with nested progress items."""
    
    stages: list[str]
    title: str = "Processing"
    current_stage: int = 0
    sub_items: list[tuple[str, ItemStatus]] = field(default_factory=list)
    _max_visible_items: int = 6
    
    def advance_stage(self) -> None:
        """Move to the next stage."""
        if self.current_stage < len(self.stages):
            self.current_stage += 1
        self.sub_items.clear()
    
    def add_item(self, name: str, status: ItemStatus = "pending") -> None:
        """Add a sub-item to track."""
        self.sub_items.append((name, status))
    
    def update_item(self, name: str, status: ItemStatus) -> None:
        """Update status of an existing item."""
        for i, (item_name, _) in enumerate(self.sub_items):
            if item_name == name:
                self.sub_items[i] = (name, status)
                return
        self.sub_items.append((name, status))
    
    def render(self) -> Panel:
        """Render the current progress state."""
        table = Table.grid(padding=(0, 2))
        table.add_column(width=3)
        table.add_column()
        
        # Render stages
        for i, stage in enumerate(self.stages):
            if i < self.current_stage:
                table.add_row("[green]✓[/green]", f"[green]{stage}[/green]")
            elif i == self.current_stage:
                table.add_row("[cyan]◉[/cyan]", f"[cyan bold]{stage}[/cyan bold]")
            else:
                table.add_row("[dim]○[/dim]", f"[dim]{stage}[/dim]")
        
        # Render sub-items (show last N)
        if self.sub_items:
            table.add_row("", "")
            visible = self.sub_items[-self._max_visible_items:]
            
            if len(self.sub_items) > self._max_visible_items:
                hidden = len(self.sub_items) - self._max_visible_items
                table.add_row("", f"[dim]  ... {hidden} more above[/dim]")
            
            for name, status in visible:
                icon, color = self._status_style(status)
                table.add_row("", f"  [{color}]{icon} {name}[/{color}]")
        
        return Panel(table, title=f"[bold]{self.title}[/bold]", border_style="cyan")
    
    def _status_style(self, status: ItemStatus) -> tuple[str, str]:
        """Get icon and color for status."""
        return {
            "pending": ("○", "dim"),
            "active": ("◉", "cyan"),
            "done": ("✓", "green"),
            "failed": ("✗", "red"),
            "skipped": ("⊘", "yellow"),
        }.get(status, ("?", "white"))


class ProgressContext:
    """Context manager for live progress display."""
    
    def __init__(self, progress: StageProgress, console: Console | None = None):
        self.progress = progress
        self.console = console or Console(stderr=True)
        self._live: Live | None = None
    
    def __enter__(self) -> "ProgressContext":
        self._live = Live(
            self.progress.render(),
            console=self.console,
            refresh_per_second=4,
            transient=True,
        )
        self._live.__enter__()
        return self
    
    def __exit__(self, *args):
        if self._live:
            self._live.__exit__(*args)
    
    def update(self) -> None:
        """Refresh the display."""
        if self._live:
            self._live.update(self.progress.render())
    
    def advance_stage(self) -> None:
        """Move to next stage and refresh."""
        self.progress.advance_stage()
        self.update()
    
    def add_item(self, name: str, status: ItemStatus = "active") -> None:
        """Add item and refresh."""
        self.progress.add_item(name, status)
        self.update()
    
    def update_item(self, name: str, status: ItemStatus) -> None:
        """Update item and refresh."""
        self.progress.update_item(name, status)
        self.update()
