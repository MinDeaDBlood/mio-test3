"""Shared appearance state for every root and Toplevel window."""

from __future__ import annotations

from tkinter import TclError
from typing import Any, Protocol, cast
from weakref import WeakSet

from src.ui.common.themes.identifiers import DARK_THEME, require_theme_id
from src.ui.common.themes.native_palette import apply_native_theme, get_theme_palette
from src.ui.common.titlebar import TitlebarWindowProtocol, set_title_bar_color


class AppearanceWindowProtocol(TitlebarWindowProtocol, Protocol):
    def winfo_exists(self) -> int: ...
    def attributes(self, *args: object) -> object: ...
    def configure(self, **kwargs: object) -> object: ...
_WINDOWS: WeakSet[AppearanceWindowProtocol] = WeakSet()
_THEME_ID = DARK_THEME
_WINDOW_ALPHA = 1.0
_MIN_ALPHA = 0.55
_MAX_ALPHA = 1.0
_DEFAULT_EFFECT_ALPHA = 0.90


def normalize_window_alpha(
    value: object,
    *,
    default: float = _DEFAULT_EFFECT_ALPHA,
) -> float:
    try:
        alpha = float(str(value))
    except (TypeError, ValueError):
        alpha = default
    return max(_MIN_ALPHA, min(alpha, _MAX_ALPHA))


def resolve_transparency_alpha(
    *,
    enabled: bool,
    effect_alpha: object = _DEFAULT_EFFECT_ALPHA,
) -> float:
    return normalize_window_alpha(effect_alpha) if enabled else 1.0


def _window_exists(window: object) -> bool:
    try:
        return bool(cast(Any, window).winfo_exists())
    except (AttributeError, TclError):
        return False


def _registered_windows() -> tuple[AppearanceWindowProtocol, ...]:
    return tuple(window for window in tuple(_WINDOWS) if _window_exists(window))


def _apply_to_window(
    window: AppearanceWindowProtocol,
    *,
    include_widget_tree: bool = True,
) -> None:
    if not _window_exists(window):
        return
    palette = get_theme_palette(_THEME_ID)
    try:
        window.configure(background=palette.window_background)
    except (AttributeError, TclError):
        pass
    if not bool(getattr(window, "_appearance_alpha_gated", False)):
        try:
            window.attributes("-alpha", _WINDOW_ALPHA)
        except (AttributeError, TclError):
            pass
    if include_widget_tree:
        try:
            apply_native_theme(window, _THEME_ID)
        except (AttributeError, TclError, TypeError):
            pass
    try:
        set_title_bar_color(window, True)
    except (AttributeError, OSError, TclError, TypeError, ValueError):
        pass


def register_window(window: object) -> None:
    """Register a window once and apply the current theme and transparency."""

    typed_window = cast(AppearanceWindowProtocol, window)
    try:
        _WINDOWS.add(typed_window)
    except TypeError:
        return

    _apply_to_window(typed_window)


def apply_theme_to_windows(theme_id: str) -> None:
    """Apply the final settled theme state exactly once to every window."""

    global _THEME_ID
    _THEME_ID = require_theme_id(theme_id)
    for window in _registered_windows():
        _apply_to_window(window)


def apply_transparency_to_windows(
    *,
    enabled: bool,
    effect_alpha: object = _DEFAULT_EFFECT_ALPHA,
) -> float:
    global _WINDOW_ALPHA
    _WINDOW_ALPHA = resolve_transparency_alpha(
        enabled=enabled,
        effect_alpha=effect_alpha,
    )
    for window in _registered_windows():
        _apply_to_window(window, include_widget_tree=False)
    return _WINDOW_ALPHA


def current_window_alpha() -> float:
    return _WINDOW_ALPHA


def current_theme_id() -> str:
    return _THEME_ID


__all__ = [
    "AppearanceWindowProtocol",
    "apply_theme_to_windows",
    "apply_transparency_to_windows",
    "current_theme_id",
    "current_window_alpha",
    "normalize_window_alpha",
    "register_window",
    "resolve_transparency_alpha",
]
