from __future__ import annotations

DARK_THEME = "dark"
LIGHT_THEME = "light"
SUPPORTED_THEMES = frozenset({DARK_THEME, LIGHT_THEME})


def normalize_theme_id(value: object) -> str:
    """Return a stable technical identifier for an interface theme."""

    theme_id = str(value).strip()
    if theme_id not in SUPPORTED_THEMES:
        raise ValueError("settings_unsupported_theme")
    return theme_id


__all__ = [
    "DARK_THEME",
    "LIGHT_THEME",
    "SUPPORTED_THEMES",
    "normalize_theme_id",
]
