"""Multi-select widget for wve TUI."""

from dataclasses import dataclass
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


@dataclass
class SelectableItem:
    """An item in the multi-select list."""
    display: str
    value: Any
    selected: bool = False
    suffix: str = ""


class MultiSelect(Widget):
    """Multi-select with toggle, all, none."""

    BINDINGS = [
        Binding("space", "toggle", "Toggle", show=False),
        Binding("a", "select_all", "All", show=False),
        Binding("n", "select_none", "None", show=False),
        Binding("tab", "preview", "Preview", show=False),
        Binding("enter", "confirm", "Confirm", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("j", "move_down", "Down", show=False),
    ]

    DEFAULT_CSS = """
    MultiSelect {
        width: 100%;
        height: auto;
    }
    
    MultiSelect > .ms-header {
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    
    MultiSelect > .ms-items {
        width: 100%;
        height: auto;
        min-height: 3;
    }
    
    MultiSelect > .ms-footer {
        width: 100%;
        height: 1;
        margin-top: 1;
        color: $text-muted;
    }
    
    MultiSelect > .ms-item {
        width: 100%;
        height: 1;
    }
    
    MultiSelect > .ms-item.--highlight {
        background: $accent;
    }
    """

    class Confirmed(Message):
        """Posted when selection is confirmed."""
        def __init__(self, selected: list[Any]) -> None:
            self.selected = selected
            super().__init__()

    class Cancelled(Message):
        """Posted when selection is cancelled."""
        pass

    class PreviewRequested(Message):
        """Posted when preview is requested."""
        def __init__(self, item: Any) -> None:
            self.item = item
            super().__init__()

    def __init__(
        self,
        items: list[tuple[str, Any, bool]],
        prompt: str = "Select items:",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.prompt = prompt
        self._items: list[SelectableItem] = []
        for display, value, preselected in items:
            parts = display.rsplit("  ", 1)
            if len(parts) == 2:
                self._items.append(SelectableItem(
                    display=parts[0],
                    value=value,
                    selected=preselected,
                    suffix=parts[1],
                ))
            else:
                self._items.append(SelectableItem(
                    display=display,
                    value=value,
                    selected=preselected,
                ))
        self._cursor = 0

    @property
    def selected_count(self) -> int:
        return sum(1 for item in self._items if item.selected)

    @property
    def selected_values(self) -> list[Any]:
        return [item.value for item in self._items if item.selected]

    def compose(self) -> ComposeResult:
        yield Static(self._render_header(), classes="ms-header")
        with Vertical(classes="ms-items"):
            for i, item in enumerate(self._items):
                yield Static(self._render_item(i), classes=f"ms-item item-{i}")
        yield Static(
            "[dim][space] toggle  [a] all  [n] none  [tab] preview  [enter] done  [esc] cancel[/dim]",
            classes="ms-footer",
        )

    def _render_header(self) -> str:
        count_str = f"{self.selected_count} selected"
        padding = max(0, 60 - len(self.prompt) - len(count_str))
        return f"{self.prompt}{' ' * padding}[cyan]{count_str}[/cyan]"

    def _render_item(self, index: int) -> str:
        item = self._items[index]
        check = "✓" if item.selected else " "
        cursor = ">" if index == self._cursor else " "
        suffix = f"  [dim]{item.suffix}[/dim]" if item.suffix else ""
        return f"{cursor} {check} {item.display}{suffix}"

    def _refresh_display(self) -> None:
        header = self.query_one(".ms-header", Static)
        header.update(self._render_header())
        for i in range(len(self._items)):
            item_widget = self.query_one(f".item-{i}", Static)
            item_widget.update(self._render_item(i))
            if i == self._cursor:
                item_widget.add_class("--highlight")
            else:
                item_widget.remove_class("--highlight")

    def action_toggle(self) -> None:
        if self._items:
            self._items[self._cursor].selected = not self._items[self._cursor].selected
            self._refresh_display()

    def action_select_all(self) -> None:
        for item in self._items:
            item.selected = True
        self._refresh_display()

    def action_select_none(self) -> None:
        for item in self._items:
            item.selected = False
        self._refresh_display()

    def action_preview(self) -> None:
        if self._items:
            self.post_message(self.PreviewRequested(self._items[self._cursor].value))

    def action_confirm(self) -> None:
        self.post_message(self.Confirmed(self.selected_values))

    def action_cancel(self) -> None:
        self.post_message(self.Cancelled())

    def action_move_up(self) -> None:
        if self._cursor > 0:
            self._cursor -= 1
            self._refresh_display()

    def action_move_down(self) -> None:
        if self._cursor < len(self._items) - 1:
            self._cursor += 1
            self._refresh_display()

    def on_mount(self) -> None:
        self._refresh_display()
