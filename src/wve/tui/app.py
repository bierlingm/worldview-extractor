"""Main Textual application for wve."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static
from textual.screen import Screen

from wve.branding import LOGO, TAGLINE
from wve.tui.wizard import WizardScreen
from wve.tui.browser import BrowserScreen
from wve.tui.ask import AskScreen
from wve.tui.keys import NAVIGATION_BINDINGS


class MainMenu(Screen):
    """Main menu screen."""
    
    BINDINGS = [
        Binding("n", "new", "New extraction", show=False),
        Binding("b", "browse", "Browse library", show=False),
        Binding("a", "ask", "Ask question", show=False),
        Binding("q", "quit", "Quit", show=False),
        *NAVIGATION_BINDINGS,
    ]
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(LOGO, id="logo")
            yield Static(f"[dim]{TAGLINE}[/dim]", id="tagline")
            yield Static("")
            yield Static("  [bold cyan]n[/] new extraction    [bold cyan]b[/] browse library    [bold cyan]a[/] ask    [bold cyan]q[/] quit", id="hints")
    
    def action_new(self) -> None:
        self.app.push_screen(WizardScreen())
    
    def action_browse(self) -> None:
        self.app.push_screen("browser")
    
    def action_ask(self) -> None:
        self.app.push_screen("ask")
    
    def action_quit(self) -> None:
        self.app.exit()


class WveApp(App):
    """Weave - Worldview Synthesis Engine."""
    
    TITLE = "Weave"
    SUB_TITLE = "Worldview Synthesis Engine"
    
    CSS = """
    Screen {
        padding: 1;
    }
    
    Input {
        width: 100%;
    }
    
    TextArea {
        width: 100%;
        height: 8;
    }
    """
    
    SCREENS = {
        "main": MainMenu,
    }
    
    def __init__(self, prefilled_state=None):
        super().__init__()
        self.prefilled_state = prefilled_state
    
    def on_mount(self) -> None:
        # Register screens that need dynamic initialization
        self.install_screen(BrowserScreen(), name="browser")
        self.install_screen(AskScreen(), name="ask")
        
        # If we have prefilled state, go directly to wizard
        if self.prefilled_state:
            wizard = WizardScreen(prefilled_state=self.prefilled_state)
            self.push_screen(wizard)
        else:
            self.push_screen("main")


def run_tui() -> None:
    """Run the TUI application."""
    app = WveApp()
    app.run()


if __name__ == "__main__":
    run_tui()
