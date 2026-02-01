"""Configuration file support for wve."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".config" / "wve" / "config.toml"

# Default configuration values
DEFAULT_KEYS = {
    "up": ["k", "up"],
    "down": ["j", "down"],
    "confirm": ["enter"],
    "back": ["q", "escape"],
}

DEFAULT_COLORS = {
    "accent": "cyan",
    "muted": "dim white",
}

DEFAULT_DEFAULTS = {
    "source": "search",
    "auto_accept_likely": False,
    "agent": "",
}


@dataclass
class WveConfig:
    """Configuration for wve."""

    keys: dict[str, list[str]] = field(default_factory=lambda: DEFAULT_KEYS.copy())
    colors: dict[str, str] = field(default_factory=lambda: DEFAULT_COLORS.copy())
    defaults: dict[str, Any] = field(default_factory=lambda: DEFAULT_DEFAULTS.copy())

    @classmethod
    def load(cls) -> "WveConfig":
        """Load from file or return defaults."""
        if not CONFIG_PATH.exists():
            return cls()

        try:
            with open(CONFIG_PATH, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            return cls()

        keys = {**DEFAULT_KEYS, **data.get("keys", {})}
        colors = {**DEFAULT_COLORS, **data.get("colors", {})}
        defaults = {**DEFAULT_DEFAULTS, **data.get("defaults", {})}

        return cls(keys=keys, colors=colors, defaults=defaults)


_config: WveConfig | None = None


def get_config() -> WveConfig:
    """Get cached config."""
    global _config
    if _config is None:
        _config = WveConfig.load()
    return _config
