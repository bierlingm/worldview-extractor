"""Single-screen inline extraction wizard for wve TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static, Input, TextArea
from textual.validation import Length

STEP_SUBJECT = "subject"
STEP_SOURCE = "source"
STEP_URLS = "urls"
STEP_CHANNEL = "channel"
STEP_CONFIRM = "confirm"


class WizardState:
    """Shared state for wizard steps."""
    
    def __init__(self):
        self.subject: str = ""
        self.source_type: str = "search"
        self.urls: list[str] = []
        self.channel_url: str = ""


class WizardScreen(Screen):
    """Single-screen inline wizard."""
    
    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("enter", "next", "Next", show=False),
        Binding("ctrl+n", "next", "Next", show=False),
        Binding("1", "source_1", "YouTube search", show=False),
        Binding("2", "source_2", "Channel URL", show=False),
        Binding("3", "source_3", "Video URLs", show=False),
        Binding("4", "source_4", "Local files", show=False),
    ]
    
    def __init__(self, prefilled_state: WizardState | None = None):
        super().__init__()
        self.state = prefilled_state or WizardState()
        
        # Determine starting step based on prefilled state
        if prefilled_state and prefilled_state.subject:
            if prefilled_state.source_type == "search":
                self.step = STEP_CONFIRM
            elif prefilled_state.source_type == "channel" and prefilled_state.channel_url:
                self.step = STEP_CONFIRM
            else:
                self.step = STEP_SOURCE
        else:
            self.step = STEP_SUBJECT
    
    def compose(self) -> ComposeResult:
        yield Vertical(id="wizard-content")
        yield Static("", id="key-hints")
    
    def on_mount(self) -> None:
        self._render_step()
    
    def _render_step(self) -> None:
        container = self.query_one("#wizard-content", Vertical)
        container.remove_children()
        
        if self.step == STEP_SUBJECT:
            self._render_subject_step(container)
        elif self.step == STEP_SOURCE:
            self._render_source_step(container)
        elif self.step == STEP_URLS:
            self._render_urls_step(container)
        elif self.step == STEP_CHANNEL:
            self._render_channel_step(container)
        elif self.step == STEP_CONFIRM:
            self._render_confirm_step(container)
        
        self._update_hints()
    
    def _render_subject_step(self, container: Vertical) -> None:
        container.mount(Static("[bold]Step 1 of 3[/bold]"))
        container.mount(Static(""))
        container.mount(Static("Who do you want to understand?"))
        container.mount(Static(""))
        input_widget = Input(
            placeholder="e.g., Naval Ravikant",
            id="subject-input",
            validators=[Length(minimum=2)],
            value=self.state.subject,
        )
        container.mount(input_widget)
        container.mount(Static(""))
        container.mount(Static("[dim]Tip: Use full names for better search results[/dim]"))
        self.call_after_refresh(lambda: input_widget.focus())
    
    def _render_source_step(self, container: Vertical) -> None:
        container.mount(Static("[bold]Step 2 of 3[/bold]"))
        container.mount(Static(""))
        container.mount(Static(f"Where should we find content about [bold]{self.state.subject}[/bold]?"))
        container.mount(Static(""))
        container.mount(Static("  [bold cyan]1[/] YouTube search"))
        container.mount(Static("  [bold cyan]2[/] YouTube channel URL"))
        container.mount(Static("  [bold cyan]3[/] Paste video URLs"))
        container.mount(Static("  [bold cyan]4[/] Local transcript files"))
        container.mount(Static(""))
        container.mount(Static("[dim]Press 1-4 to select source type[/dim]"))
    
    def _render_urls_step(self, container: Vertical) -> None:
        container.mount(Static("[bold]Step 2b: Enter URLs[/bold]"))
        container.mount(Static(""))
        container.mount(Static("Paste YouTube URLs (one per line)"))
        container.mount(Static(""))
        textarea = TextArea(id="urls-input", text="\n".join(self.state.urls))
        container.mount(textarea)
        container.mount(Static(""))
        container.mount(Static("[dim]Tip: You can paste multiple URLs[/dim]"))
        self.call_after_refresh(lambda: textarea.focus())
    
    def _render_channel_step(self, container: Vertical) -> None:
        container.mount(Static("[bold]Step 2b: Enter Channel[/bold]"))
        container.mount(Static(""))
        container.mount(Static("Enter the YouTube channel URL"))
        container.mount(Static(""))
        input_widget = Input(
            placeholder="https://youtube.com/@channel",
            id="channel-input",
            value=self.state.channel_url,
        )
        container.mount(input_widget)
        container.mount(Static(""))
        container.mount(Static("[dim]Example: https://youtube.com/@naval[/dim]"))
        self.call_after_refresh(lambda: input_widget.focus())
    
    def _render_confirm_step(self, container: Vertical) -> None:
        container.mount(Static("[bold]Step 3 of 3: Confirm[/bold]"))
        container.mount(Static(""))
        container.mount(Static("Ready to extract worldview for:"))
        container.mount(Static(""))
        container.mount(Static(f"  [bold]{self.state.subject}[/bold]"))
        container.mount(Static(""))
        container.mount(Static(f"  Source: [dim]{self._source_description()}[/dim]"))
        container.mount(Static(""))
        container.mount(Static(f"  Command: [cyan]{self._build_command()}[/cyan]"))
    
    def _update_hints(self) -> None:
        hints = self.query_one("#key-hints", Static)
        if self.step == STEP_SUBJECT:
            hints.update("[bold cyan]esc[/] cancel  [bold cyan]enter[/] next")
        elif self.step == STEP_SOURCE:
            hints.update("[bold cyan]1-4[/] select  [bold cyan]esc[/] back")
        elif self.step == STEP_URLS:
            hints.update("[bold cyan]esc[/] back  [bold cyan]ctrl+n[/] next")
        elif self.step == STEP_CONFIRM:
            hints.update("[bold cyan]esc[/] back  [bold cyan]enter[/] run extraction")
        else:
            hints.update("[bold cyan]esc[/] back  [bold cyan]enter[/] next")
    
    def _source_description(self) -> str:
        if self.state.source_type == "search":
            return f"YouTube search for '{self.state.subject}'"
        elif self.state.source_type == "channel":
            return f"Channel: {self.state.channel_url}"
        elif self.state.source_type == "urls":
            return f"{len(self.state.urls)} video URL(s)"
        else:
            return "Local files"
    
    def _build_command(self) -> str:
        subject_quoted = f'"{self.state.subject}"'
        
        if self.state.source_type == "search":
            # Full pipeline: discover -> auto-accept likely -> fetch -> analyze
            cmd_parts = ["wve", "-S", subject_quoted, "-s", "-y"]
        elif self.state.source_type == "channel":
            # from-channel downloads transcripts, then run analysis
            cmd_parts = ["wve", "from-channel", self.state.channel_url, "-o", "transcripts"]
            cmd_parts.append("&&")
            cmd_parts.extend(["wve", "run", "transcripts", "-s", subject_quoted, "--report-only"])
        elif self.state.source_type == "urls":
            cmd_parts = ["wve", "run", "-s", subject_quoted]
            for url in self.state.urls:
                cmd_parts.extend(["-u", url])
        else:
            cmd_parts = ["wve", "run", "-s", subject_quoted, "./transcripts/"]
        
        return " ".join(cmd_parts)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.step in (STEP_SUBJECT, STEP_CHANNEL):
            self.action_next()
    
    def _select_source(self, source_type: str) -> None:
        """Select source type and advance."""
        if self.step != STEP_SOURCE:
            return
        self.state.source_type = source_type
        if source_type == "urls":
            self.step = STEP_URLS
        elif source_type == "channel":
            self.step = STEP_CHANNEL
        else:
            self.step = STEP_CONFIRM
        self._render_step()
    
    def action_source_1(self) -> None:
        self._select_source("search")
    
    def action_source_2(self) -> None:
        self._select_source("channel")
    
    def action_source_3(self) -> None:
        self._select_source("urls")
    
    def action_source_4(self) -> None:
        self._select_source("files")
    
    def action_back(self) -> None:
        if self.step == STEP_SUBJECT:
            self.app.pop_screen()
        elif self.step == STEP_SOURCE:
            self.step = STEP_SUBJECT
            self._render_step()
        elif self.step in (STEP_URLS, STEP_CHANNEL):
            self.step = STEP_SOURCE
            self._render_step()
        elif self.step == STEP_CONFIRM:
            if self.state.source_type == "urls":
                self.step = STEP_URLS
            elif self.state.source_type == "channel":
                self.step = STEP_CHANNEL
            else:
                self.step = STEP_SOURCE
            self._render_step()
    
    def action_next(self) -> None:
        if self.step == STEP_SUBJECT:
            try:
                input_widget = self.query_one("#subject-input", Input)
                if input_widget.value and len(input_widget.value) >= 2:
                    self.state.subject = input_widget.value
                    self.step = STEP_SOURCE
                    self._render_step()
            except Exception:
                pass
        
        elif self.step == STEP_SOURCE:
            # Source selection is handled by 1-4 keys, not enter
            pass
        
        elif self.step == STEP_URLS:
            try:
                textarea = self.query_one("#urls-input", TextArea)
                urls = [u.strip() for u in textarea.text.split("\n") if u.strip()]
                self.state.urls = urls
                self.step = STEP_CONFIRM
                self._render_step()
            except Exception:
                pass
        
        elif self.step == STEP_CHANNEL:
            try:
                input_widget = self.query_one("#channel-input", Input)
                self.state.channel_url = input_widget.value
                self.step = STEP_CONFIRM
                self._render_step()
            except Exception:
                pass
        
        elif self.step == STEP_CONFIRM:
            from wve.tui.execution import ExecutionScreen
            self.app.push_screen(ExecutionScreen(self.state))
