"""fzf-style fuzzy select widget for Textual."""

from typing import Any
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Input


def fuzzy_match(query: str, text: str) -> bool:
    """Simple fuzzy matching - all query chars must appear in order."""
    if not query:
        return True
    query = query.lower()
    text = text.lower()
    qi = 0
    for char in text:
        if char == query[qi]:
            qi += 1
            if qi == len(query):
                return True
    return False


class FuzzySelect(Widget):
    """fzf-style fuzzy selector."""
    
    BINDINGS = [
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("enter", "select", "Select", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]
    
    class Selected(Message):
        """Posted when an item is selected."""
        def __init__(self, value: Any, display: str) -> None:
            self.value = value
            self.display = display
            super().__init__()
    
    class Cancelled(Message):
        """Posted when selection is cancelled."""
        pass
    
    def __init__(
        self,
        items: list[tuple[str, Any]],
        prompt: str = ">",
        max_visible: int = 10,
    ) -> None:
        """
        Args:
            items: list of (display_text, value) tuples
            prompt: prompt character
            max_visible: max items to show at once
        """
        super().__init__()
        self.all_items = items
        self.filtered_items = list(items)
        self.prompt = prompt
        self.max_visible = max_visible
        self.cursor = 0
        self.query = ""
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(placeholder="type to filter...", id="fuzzy-input")
            yield Static(id="fuzzy-count")
            yield Static(id="fuzzy-list")
            yield Static(
                "[dim][↑↓/jk] move  [enter] select  [esc] cancel[/dim]",
                id="fuzzy-hints",
            )
    
    def on_mount(self) -> None:
        self.query_one("#fuzzy-input", Input).focus()
        self._update_display()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        self.query = event.value
        self._filter_items()
        self._update_display()
    
    def _filter_items(self) -> None:
        if not self.query:
            self.filtered_items = list(self.all_items)
        else:
            self.filtered_items = [
                item for item in self.all_items
                if fuzzy_match(self.query, item[0])
            ]
        self.cursor = 0
    
    def _update_display(self) -> None:
        count_widget = self.query_one("#fuzzy-count", Static)
        count_widget.update(f"  {len(self.filtered_items)}/{len(self.all_items)}")
        
        list_widget = self.query_one("#fuzzy-list", Static)
        if not self.filtered_items:
            list_widget.update("  [dim]no matches[/dim]")
            return
        
        start = max(0, self.cursor - self.max_visible // 2)
        end = min(len(self.filtered_items), start + self.max_visible)
        if end - start < self.max_visible:
            start = max(0, end - self.max_visible)
        
        lines = []
        for i in range(start, end):
            display_text = self.filtered_items[i][0]
            if i == self.cursor:
                lines.append(f"{self.prompt} [bold reverse]{display_text}[/bold reverse]")
            else:
                lines.append(f"  {display_text}")
        
        list_widget.update("\n".join(lines))
    
    def action_move_up(self) -> None:
        if self.filtered_items and self.cursor > 0:
            self.cursor -= 1
            self._update_display()
    
    def action_move_down(self) -> None:
        if self.filtered_items and self.cursor < len(self.filtered_items) - 1:
            self.cursor += 1
            self._update_display()
    
    def action_select(self) -> None:
        if self.filtered_items:
            item = self.filtered_items[self.cursor]
            self.post_message(self.Selected(value=item[1], display=item[0]))
    
    def action_cancel(self) -> None:
        self.post_message(self.Cancelled())
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_select()
