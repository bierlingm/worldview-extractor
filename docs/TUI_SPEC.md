# WVE Terminal UI Overhaul Specification

## Decision: Textual + Rich

**Why Textual over Bubbletea:**
- wve is Python; Bubbletea requires Go rewrite
- Textual supports browser deployment (future web UI)
- Textual has CSS-based theming (easier iteration)
- Can still adopt Charm's visual aesthetic

---

## Phase 1: Foundation (Quick Wins)

### 1.1 Color Theme System

```python
# wve/theme.py
from rich.theme import Theme

WVE_THEME = Theme({
    "wve.primary": "cyan",
    "wve.success": "green",
    "wve.warning": "yellow", 
    "wve.error": "red",
    "wve.muted": "dim white",
    "wve.accent": "magenta",
    "wve.highlight": "bold cyan",
    "wve.quote": "italic white",
    "wve.source": "dim cyan",
})

def get_console():
    from rich.console import Console
    return Console(theme=WVE_THEME, stderr=True)
```

### 1.2 Branding

```python
# wve/branding.py
LOGO = """
[cyan]╦ ╦╔═╗╔═╗╦  ╦╔═╗[/cyan]
[cyan]║║║║╣ ╠═╣╚╗╔╝║╣ [/cyan]
[cyan]╚╩╝╚═╝╩ ╩ ╚╝ ╚═╝[/cyan]
[dim]Worldview Synthesis Engine[/dim]
"""

TAGLINE = "Synthesize intellectual worldviews from any source"
```

### 1.3 Completion Panel Factory

```python
# wve/ui/panels.py
from rich.panel import Panel
from rich.table import Table

def completion_panel(
    title: str,
    stats: dict[str, str | int],
    next_steps: list[tuple[str, str]],  # (command, description)
    style: str = "green"
) -> Panel:
    """Consistent completion panels across all commands."""
    content = []
    
    # Stats section
    for key, value in stats.items():
        content.append(f"[bold]{key}:[/bold] {value}")
    
    content.append("")
    content.append("[bold]What's next?[/bold]")
    for cmd, desc in next_steps:
        content.append(f"  [cyan]{cmd}[/cyan]")
        content.append(f"      {desc}")
    
    return Panel(
        "\n".join(content),
        title=f"[{style}]✓ {title}[/{style}]",
        border_style=style,
    )
```

---

## Phase 2: Interactive Wizard

### 2.1 Main Menu (Textual App)

```python
# wve/tui/app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, Vertical

class WveApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    #menu {
        width: 60;
        height: auto;
        border: round cyan;
        padding: 1 2;
    }
    Button {
        width: 100%;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "new", "New extraction"),
        ("b", "browse", "Browse library"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="menu"):
            yield Static(LOGO)
            yield Button("🔍 New extraction", id="new", variant="primary")
            yield Button("📚 Browse library", id="browse")
            yield Button("💬 Ask a question", id="ask")
            yield Button("⚙️  Settings", id="settings")
            yield Static("\n[dim]Recent:[/dim]")
            yield Static("[dim]  Naval Ravikant (3h ago)[/dim]")
        yield Footer()
```

### 2.2 New Extraction Wizard

Multi-step form:
1. Subject name input
2. Source selection (URL paste, file browse, channel scrape)
3. Options (language, depth)
4. Confirmation & run

```python
# wve/tui/wizard.py
from textual.app import App
from textual.widgets import Input, RadioSet, RadioButton, ProgressBar
from textual.screen import Screen

class SubjectScreen(Screen):
    def compose(self):
        yield Static("Who do you want to understand?")
        yield Input(placeholder="e.g., Naval Ravikant", id="subject")
        yield Static("[dim]Tip: Use full names for better search results[/dim]")

class SourceScreen(Screen):
    def compose(self):
        yield Static("Where should we find their content?")
        yield RadioSet(
            RadioButton("YouTube search", id="search"),
            RadioButton("YouTube channel URL", id="channel"),
            RadioButton("Paste URLs", id="urls"),
            RadioButton("Local files", id="files"),
        )
```

---

## Phase 3: Rich Progress System

### 3.1 Multi-Stage Progress

```python
# wve/ui/progress.py
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

class StageProgress:
    """Track multi-stage operations with nested progress."""
    
    def __init__(self, stages: list[str]):
        self.stages = stages
        self.current = 0
        self.sub_items: list[tuple[str, str]] = []  # (name, status)
    
    def render(self) -> Table:
        table = Table.grid(padding=(0, 1))
        
        # Stage overview
        for i, stage in enumerate(self.stages):
            if i < self.current:
                table.add_row("✓", f"[green]{stage}[/green]")
            elif i == self.current:
                table.add_row("◉", f"[cyan bold]{stage}[/cyan bold]")
            else:
                table.add_row("○", f"[dim]{stage}[/dim]")
        
        # Sub-items for current stage
        if self.sub_items:
            table.add_row("", "")
            for name, status in self.sub_items[-5:]:
                icon = {"done": "✓", "active": "◉", "failed": "✗"}.get(status, "○")
                color = {"done": "green", "active": "cyan", "failed": "red"}.get(status, "dim")
                table.add_row("", f"  [{color}]{icon} {name}[/{color}]")
        
        return table
```

### 3.2 Usage in Commands

```python
# In run command:
with Live(progress.render(), refresh_per_second=4, console=console) as live:
    progress.advance_stage()  # "Downloading transcripts"
    
    for url in urls:
        progress.add_item(vid_id, "active")
        live.update(progress.render())
        
        result = download_transcript(url, ...)
        
        progress.update_item(vid_id, "done" if result else "failed")
        live.update(progress.render())
    
    progress.advance_stage()  # "Analyzing content"
    ...
```

---

## Phase 4: Command Simplification

### 4.1 New Command Structure

```
wve                     # Interactive TUI (Textual app)
wve run                 # Primary CLI entry point
wve ask                 # Query existing worldview
wve store               # Library management
wve identity            # Subject profiles

# Hidden/deprecated (still work, not in --help)
wve pipeline
wve search  
wve transcripts
wve extract
wve cluster
wve synthesize
```

### 4.2 Implementation

```python
# cli.py
@main.command(hidden=True)  # Hide from --help
def pipeline(...):
    """[Deprecated] Use 'wve run' instead."""
    click.echo("Note: 'wve pipeline' is deprecated. Use 'wve run' instead.", err=True)
    # ... existing implementation
```

### 4.3 Default Interactive Mode

```python
@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx, debug):
    if ctx.invoked_subcommand is None:
        # No subcommand = launch TUI
        from wve.tui.app import WveApp
        app = WveApp()
        app.run()
```

---

## Phase 5: Full TUI Browser

### 5.1 Library Browser (Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│ WEAVE · Library                                        [q]uit  │
├────────────────────────┬────────────────────────────────────────┤
│ Subjects               │ Naval Ravikant                         │
│ ──────────────────     │ ════════════════════════════════════   │
│ > Naval Ravikant       │                                        │
│   Tyler Cowen          │ Sources: 47 transcripts (12.3h)        │
│   Balaji Srinivasan    │ Quotes: 892 notable · 127 contrarian   │
│   Paul Graham          │ Updated: 2026-01-28                    │
│                        │                                        │
│                        │ Top Themes                             │
│                        │ ──────────                             │
│                        │ • Wealth (234x)                        │
│                        │ • Happiness (189x)                     │
│                        │ • Leverage (156x)                      │
│                        │ • Reading (142x)                       │
│                        │                                        │
│                        │ Sample Quote                           │
│                        │ ──────────                             │
│                        │ "Seek wealth, not money or status.     │
│                        │  Wealth is having assets that earn     │
│                        │  while you sleep."                     │
│                        │                                        │
│ [n]ew  [a]sk  [d]elete │ [enter] Full report  [e]xport         │
└────────────────────────┴────────────────────────────────────────┘
```

### 5.2 Ask Interface

Real-time streaming responses with source highlighting:

```
┌─────────────────────────────────────────────────────────────────┐
│ Ask: Naval Ravikant                                    [esc]   │
├─────────────────────────────────────────────────────────────────┤
│ > What does Naval think about formal education?                │
│                                                                │
│ Naval is generally skeptical of traditional formal education.  │
│ He believes that:                                              │
│                                                                │
│ 1. Self-education through reading is more valuable than        │
│    credentials [source: podcast-ep-42]                         │
│                                                                │
│ 2. The education system optimizes for compliance rather        │
│    than creativity [source: interview-2023]                    │
│                                                                │
│ ─────────────────────────────────────────────────────          │
│ Sources: podcast-ep-42, interview-2023, tim-ferriss-show       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Order

| Week | Tasks |
|------|-------|
| 1 | Theme system, branding, completion panels |
| 2 | StageProgress class, apply to `run` command |
| 3 | Command deprecation, default TUI launcher |
| 4 | Textual: Main menu + new extraction wizard |
| 5 | Textual: Library browser |
| 6 | Textual: Ask interface with streaming |
| 7 | Polish, animations, edge cases |

---

## Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
tui = [
    "textual>=0.50.0",
    "textual-dev>=1.0.0",  # For hot reload during dev
]
```

Install: `pip install wve[tui]`

---

## Design Principles (Charm-Inspired)

1. **Soft borders** - Use `round` border style, not sharp corners
2. **Muted backgrounds** - Dark grays, not pure black
3. **Accent sparingly** - Cyan for interactive, green for success
4. **Motion with purpose** - Spinners during work, not decoration
5. **Progressive disclosure** - Show summary, expand on demand
6. **Keyboard-first** - Every action has a hotkey
7. **Fail gracefully** - Errors in panels, not stack traces
