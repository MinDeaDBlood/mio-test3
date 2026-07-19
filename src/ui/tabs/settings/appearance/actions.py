from __future__ import annotations

from io import BytesIO

import sv_ttk
from PIL.Image import open as open_img

from src.ui.assets.loading_indicator import get_loading_indicator
from src.ui.common.window_appearance import (
    apply_theme_to_windows,
    apply_transparency_to_windows,
    register_window,
)


def _apply_theme_once(*, window, theme_id: str) -> None:
    """Match the stable original order without covers or focus changes."""

    sv_ttk.set_theme(theme_id)
    window.update_idletasks()
    apply_theme_to_windows(theme_id)
    window.update_idletasks()


def apply_initial_appearance(
    *,
    window,
    theme_var,
    language_var,
    theme_id: str,
    language_name: str,
    transparent_enabled: bool,
    effect_alpha: float | str,
) -> None:
    theme_var.set(theme_id)
    language_var.set(language_name)
    register_window(window)
    _apply_theme_once(window=window, theme_id=theme_id)
    apply_transparency_to_windows(
        enabled=transparent_enabled,
        effect_alpha=effect_alpha,
    )


def apply_theme_appearance(*, window, animation, theme_id: str) -> None:
    register_window(window)
    _apply_theme_once(window=window, theme_id=theme_id)
    image_data = get_loading_indicator(theme_id)
    animation.load_gif(open_img(BytesIO(image_data)))


def apply_transparency_appearance(*, enabled: bool, effect_alpha: float | str) -> float:
    return apply_transparency_to_windows(enabled=enabled, effect_alpha=effect_alpha)


__all__ = [
    'apply_initial_appearance',
    'apply_theme_appearance',
    'apply_transparency_appearance',
]
