"""Inline progress bars for CLI and TUI use."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, MofNCompleteColumn
from textual.widget import Widget
from textual.reactive import reactive


@contextmanager
def progress_bar(
    total: int,
    description: str = "Processing",
    current_item: str | None = None,
    console: Console | None = None,
) -> Iterator[Callable[[str | None], None]]:
    """
    Simple inline progress bar context manager.

    Format: Fetching... ████████░░░░ 8/12 [current-file.txt]

    Usage:
        with progress_bar(len(videos), "Fetching transcripts") as update:
            for video in videos:
                update(current_item=video.title)
                fetch(video)
    """
    console = console or Console(stderr=True)

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=20),
        MofNCompleteColumn(),
        TextColumn("[dim]{task.fields[current]}[/dim]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            f"{description}...",
            total=total,
            current=f"[{current_item}]" if current_item else "",
        )

        def update(current_item: str | None = None) -> None:
            progress.update(
                task,
                advance=1,
                current=f"[{current_item}]" if current_item else "",
            )

        yield update


class InlineProgress(Widget):
    """Inline progress bar widget for Textual TUI.

    Visual: Fetching... ████████░░░░ 8/12 [current-file.txt]
    """

    DEFAULT_CSS = """
    InlineProgress {
        height: 1;
        width: 100%;
    }
    """

    completed: reactive[int] = reactive(0)
    current_item: reactive[str] = reactive("")

    def __init__(
        self,
        total: int,
        description: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.total = total
        self.description = description

    def advance(self, current_item: str = "") -> None:
        """Advance progress by one and optionally update current item."""
        self.completed += 1
        self.current_item = current_item

    def render(self) -> str:
        filled = int((self.completed / max(self.total, 1)) * 12)
        bar = "█" * filled + "░" * (12 - filled)
        item_part = f" [{self.current_item}]" if self.current_item else ""
        desc = f"{self.description}... " if self.description else ""
        return f"{desc}{bar} {self.completed}/{self.total}{item_part}"
