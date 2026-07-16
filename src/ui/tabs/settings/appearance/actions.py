from __future__ import annotations

from io import BytesIO

import sv_ttk
from PIL.Image import open as open_img

from src.ui.assets import images
from src.ui.common.window_appearance import (
    apply_theme_to_windows,
    apply_transparency_to_windows,
    register_window,
)


def apply_initial_appearance(
    *,
    window,
    theme_var,
    language_var,
    theme_name: str,
    language_name: str,
    transparent_enabled: bool,
    effect_alpha: float | str,
) -> None:
    theme_var.set(theme_name)
    language_var.set(language_name)
    sv_ttk.set_theme(theme_name)
    register_window(window)
    apply_theme_to_windows(theme_name)
    apply_transparency_to_windows(
        enabled=transparent_enabled,
        effect_alpha=effect_alpha,
    )


def apply_theme_appearance(*, window, animation, theme_name: str, loading_variant: str) -> None:
    sv_ttk.set_theme(theme_name)
    register_window(window)
    apply_theme_to_windows(theme_name)
    image_data = getattr(images, f'loading_{loading_variant}_byte')
    animation.load_gif(open_img(BytesIO(image_data)))


def apply_transparency_appearance(*, enabled: bool, effect_alpha: float | str) -> float:
    return apply_transparency_to_windows(enabled=enabled, effect_alpha=effect_alpha)


__all__ = [
    'apply_initial_appearance',
    'apply_theme_appearance',
    'apply_transparency_appearance',
]
