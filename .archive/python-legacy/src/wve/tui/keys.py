"""Standard keybindings for wve TUI."""

from textual.binding import Binding

from wve.config import get_config


def _get_keys() -> dict:
    return get_config().keys


# Navigation keys (functions to read from config)
def _nav_up() -> list[str]:
    keys = _get_keys()
    return keys.get("up", ["k", "up"])


def _nav_down() -> list[str]:
    keys = _get_keys()
    return keys.get("down", ["j", "down"])


# Static navigation keys for left/right (not yet in config)
NAV_LEFT = ["left", "h"]
NAV_RIGHT = ["right", "l"]


# Action keys (functions to read from config)
def _confirm_keys() -> list[str]:
    keys = _get_keys()
    return keys.get("confirm", ["enter"])


def _back_keys() -> list[str]:
    keys = _get_keys()
    return keys.get("back", ["q", "escape"])


# Legacy module-level constants for compatibility
NAV_UP = ["up", "k"]
NAV_DOWN = ["down", "j"]
CONFIRM = ["enter"]
BACK = ["escape", "q"]
TOGGLE = ["space"]
PREVIEW = ["tab"]
HELP = ["question_mark"]
SELECT_ALL = ["a"]
SELECT_NONE = ["n"]


def make_bindings(spec: dict) -> list[Binding]:
    """Create Textual bindings from a spec dict.
    
    Args:
        spec: Dict mapping action names to (key, description) or (key, description, show) tuples.
              Example: {"next": ("j", "Next item"), "prev": ("k", "Previous item", False)}
    
    Returns:
        List of Textual Binding objects.
    """
    bindings = []
    for action, value in spec.items():
        if len(value) == 2:
            key, description = value
            show = True
        else:
            key, description, show = value
        bindings.append(Binding(key, action, description, show=show))
    return bindings


def make_nav_bindings(action_up: str, action_down: str, show: bool = False) -> list[Binding]:
    """Create navigation bindings for up/down with vim keys."""
    bindings = []
    for key in _nav_up():
        bindings.append(Binding(key, action_up, "Previous", show=show))
    for key in _nav_down():
        bindings.append(Binding(key, action_down, "Next", show=show))
    return bindings


def make_back_bindings(action: str = "back", description: str = "Back") -> list[Binding]:
    """Create back/cancel bindings for escape and q."""
    return [Binding(key, action, description, show=(key == "escape")) for key in _back_keys()]


# Common binding sets
NAVIGATION_BINDINGS = make_nav_bindings("focus_previous", "focus_next")

LIST_BINDINGS = [
    *make_nav_bindings("cursor_up", "cursor_down"),
    Binding("enter", "select_cursor", "Select"),
]

CONFIRM_BACK_BINDINGS = [
    Binding("enter", "confirm", "Confirm"),
    *make_back_bindings(),
]
