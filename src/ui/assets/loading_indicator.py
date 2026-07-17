from __future__ import annotations

from src.ui.common.themes.identifiers import (
    DARK_THEME,
    LIGHT_THEME,
    require_theme_id,
)
from src.ui.assets import images

_LOADING_INDICATORS: dict[str, bytes] = {
    DARK_THEME: images.loading_indicator_dark,
    LIGHT_THEME: images.loading_indicator_light,
}


def get_loading_indicator(theme_id: str) -> bytes:
    """Return the loading indicator used by the selected interface theme."""

    return _LOADING_INDICATORS[require_theme_id(theme_id)]


__all__ = ["get_loading_indicator"]
