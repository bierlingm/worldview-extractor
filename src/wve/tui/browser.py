"""Library browser for wve TUI."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, ListView, ListItem, Label

from wve.prompts.fuzzy_select import FuzzySelect


class WorldviewItem(ListItem):
    """A worldview entry in the list."""
    
    def __init__(self, slug: str, display_name: str, source_count: int):
        super().__init__()
        self.slug = slug
        self.display_name = display_name
        self.source_count = source_count
    
    def compose(self) -> ComposeResult:
        yield Label(f"{self.display_name} [dim]({self.source_count})[/dim]")


class BrowserApp(App):
    """Standalone app for browsing worldviews with fuzzy search."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new", "New"),
        Binding("a", "ask", "Ask"),
        Binding("d", "delete", "Delete"),
        Binding("enter", "view", "View"),
    ]
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #browser-main {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    FuzzySelect {
        height: auto;
        max-height: 80%;
    }
    
    #detail-pane {
        margin-top: 1;
        padding: 1;
        border: solid $primary;
    }
    
    #footer {
        dock: bottom;
        height: 1;
        background: $primary;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.entries = []
        self.selected_entry = None
    
    def compose(self) -> ComposeResult:
        with Vertical(id="browser-main"):
            yield Static("[bold]Worldview Library[/bold]\n", id="title")
            yield Static("", id="fuzzy-container")
            yield Static("", id="detail-pane")
        yield Static("[q] quit  [n] new  [a] ask  [d] delete  [enter] view", id="footer")
    
    def on_mount(self) -> None:
        self._load_entries()
    
    def _load_entries(self) -> None:
        """Load worldview entries and create fuzzy selector."""
        try:
            from wve.store import list_entries
            self.entries = list_entries()
        except Exception:
            self.entries = []
        
        container = self.query_one("#fuzzy-container", Static)
        
        if not self.entries:
            container.update("[dim]No worldviews stored yet. Run 'wve run' to create one.[/dim]")
            return
        
        # Build items for FuzzySelect: (display_text, value)
        items = [
            (f"{e.display_name} ({e.source_count} sources)", e.slug)
            for e in self.entries
        ]
        
        # Mount FuzzySelect
        fuzzy = FuzzySelect(items, prompt=">", max_visible=15)
        container.remove()
        self.query_one("#browser-main").mount(fuzzy, before="#detail-pane")
    
    def on_fuzzy_select_selected(self, event: FuzzySelect.Selected) -> None:
        """Handle selection from fuzzy search."""
        self._show_entry(event.value)
    
    def _show_entry(self, slug: str) -> None:
        """Show details for selected entry."""
        try:
            from wve.store import load_entry
            entry = load_entry(slug)
            self.selected_entry = entry
        except Exception:
            return
        
        # Build detail view
        lines = [
            f"[bold cyan]{entry.display_name}[/bold cyan]",
            "",
            f"[bold]Sources:[/bold] {entry.source_count} transcripts",
            f"[bold]Quotes:[/bold] {entry.quote_count} notable",
        ]
        
        if entry.themes:
            theme_names = [t.get('name', '') for t in entry.themes[:5]]
            lines.append(f"[bold]Themes:[/bold] {', '.join(theme_names)}")
        
        if entry.top_quotes:
            quote = entry.top_quotes[0]
            quote_text = quote.get('text', '')[:120]
            if len(quote.get('text', '')) > 120:
                quote_text += "..."
            lines.append("")
            lines.append(f"[italic]\"{quote_text}\"[/italic]")
        
        self.query_one("#detail-pane", Static).update("\n".join(lines))
    
    def action_view(self) -> None:
        """Open full report."""
        if self.selected_entry and self.selected_entry.report_path:
            import subprocess
            subprocess.run(["open", self.selected_entry.report_path], check=False)
    
    def action_ask(self) -> None:
        """Placeholder for ask functionality."""
        pass
    
    def action_delete(self) -> None:
        """Delete the selected entry."""
        if self.selected_entry:
            from wve.store import delete_entry
            delete_entry(self.selected_entry.slug)
            self.selected_entry = None
            self._load_entries()
    
    def action_new(self) -> None:
        """Placeholder for new worldview creation."""
        pass


class BrowserScreen(Screen):
    """Library browser with split-pane view."""
    
    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("q", "back", "Back", show=False),
        Binding("n", "new", "New", show=False),
        Binding("a", "ask", "Ask", show=False),
        Binding("d", "delete", "Delete", show=False),
        Binding("enter", "view", "View", show=False),
    ]
    
    CSS = """
    #browser-container {
        width: 100%;
        height: 100%;
    }
    
    #list-pane {
        width: 30;
        height: 100%;
        padding: 0 1;
    }
    
    #detail-pane {
        width: 1fr;
        height: 100%;
        padding: 1 2;
        margin-left: 1;
    }
    
    ListView {
        height: 1fr;
    }
    
    #stats {
        margin: 1 0;
    }
    
    #themes {
        margin: 1 0;
    }
    
    #quote-section {
        margin: 1 0;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.selected_entry = None
        self.entries = []
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="browser-container"):
            with Vertical(id="list-pane"):
                yield Static("[bold]Worldviews[/bold]")
                yield ListView(id="entry-list")
            with Vertical(id="detail-pane"):
                yield Static("", id="detail-title")
                yield Static("", id="stats")
                yield Static("", id="themes")
                yield Static("", id="quote-section")
        yield Static("[q] back  [n] new  [a] ask  [d] delete  [enter] view")
    
    def on_mount(self) -> None:
        self._load_entries()
        list_view = self.query_one("#entry-list", ListView)
        list_view.focus()
    
    def _load_entries(self) -> None:
        """Load worldview entries from store."""
        try:
            from wve.store import list_entries
            self.entries = list_entries()
        except Exception:
            self.entries = []
        
        list_view = self.query_one("#entry-list", ListView)
        list_view.clear()
        
        if not self.entries:
            list_view.append(ListItem(Label("[dim]No worldviews yet[/dim]")))
        else:
            for entry in self.entries:
                list_view.append(WorldviewItem(
                    slug=entry.slug,
                    display_name=entry.display_name,
                    source_count=entry.source_count,
                ))
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection change."""
        if isinstance(event.item, WorldviewItem):
            self._show_entry(event.item.slug)
    
    def _show_entry(self, slug: str) -> None:
        """Show details for selected entry."""
        try:
            from wve.store import load_entry
            entry = load_entry(slug)
            self.selected_entry = entry
        except Exception:
            return
        
        # Update detail pane
        self.query_one("#detail-title", Static).update(
            f"[bold cyan]{entry.display_name}[/bold cyan]"
        )
        
        stats = f"""[bold]Sources:[/bold] {entry.source_count} transcripts
[bold]Quotes:[/bold] {entry.quote_count} notable"""
        if hasattr(entry, 'updated_at') and entry.updated_at:
            stats += f"\n[bold]Updated:[/bold] {entry.updated_at.strftime('%Y-%m-%d')}"
        self.query_one("#stats", Static).update(stats)
        
        # Themes
        if entry.themes:
            theme_names = [t.get('name', '') for t in entry.themes[:5]]
            themes_text = "[bold]Top Themes[/bold]\n" + "\n".join(
                f"  • {name}" for name in theme_names if name
            )
            self.query_one("#themes", Static).update(themes_text)
        
        # Sample quote
        if entry.top_quotes:
            quote = entry.top_quotes[0]
            quote_text = quote.get('text', '')[:150]
            if len(quote.get('text', '')) > 150:
                quote_text += "..."
            self.query_one("#quote-section", Static).update(
                f"[bold]Sample Quote[/bold]\n[italic]\"{quote_text}\"[/italic]"
            )
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_view(self) -> None:
        """Open full report."""
        if self.selected_entry and self.selected_entry.report_path:
            import subprocess
            subprocess.run(["open", self.selected_entry.report_path], check=False)
    
    def action_ask(self) -> None:
        """Switch to ask screen for this entry."""
        if self.selected_entry:
            self.app.push_screen("ask")
    
    def action_delete(self) -> None:
        """Delete the selected entry."""
        if self.selected_entry:
            from wve.store import delete_entry
            delete_entry(self.selected_entry.slug)
            self.selected_entry = None
            self._load_entries()
    
    def action_new(self) -> None:
        self.app.push_screen("wizard")
