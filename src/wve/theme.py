from rich.theme import Theme
from rich.console import Console

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

def get_console(stderr: bool = True) -> Console:
    """Get a themed console for wve output."""
    return Console(theme=WVE_THEME, stderr=stderr)
