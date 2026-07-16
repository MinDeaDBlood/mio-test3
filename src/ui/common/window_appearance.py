"""Shared appearance state for every root and Toplevel window."""

from __future__ import annotations

from tkinter import TclError
from collections.abc import Callable
from typing import Protocol, cast
from weakref import WeakSet

from src.ui.common.titlebar import TitlebarWindowProtocol, set_title_bar_color


class AppearanceWindowProtocol(TitlebarWindowProtocol, Protocol):
    def winfo_exists(self) -> int: ...
    def attributes(self, *args: object) -> object: ...
    def configure(self, **kwargs: object) -> object: ...
    def bind(self, sequence: str, func: Callable[[object], object], add: str | None = None) -> object: ...
    def after_idle(self, func: Callable[[], object]) -> object: ...


_WINDOWS: WeakSet[AppearanceWindowProtocol] = WeakSet()
_BOUND_WINDOWS: WeakSet[AppearanceWindowProtocol] = WeakSet()
_THEME_NAME = 'dark'
_WINDOW_ALPHA = 1.0
_MIN_ALPHA = 0.55
_MAX_ALPHA = 1.0
_DEFAULT_EFFECT_ALPHA = 0.90
_DARK_BACKGROUND = '#101010'
_LIGHT_BACKGROUND = '#f0f0f0'


def normalize_window_alpha(value: object, *, default: float = _DEFAULT_EFFECT_ALPHA) -> float:
    try:
        alpha = float(str(value))
    except (TypeError, ValueError):
        alpha = default
    return max(_MIN_ALPHA, min(alpha, _MAX_ALPHA))


def resolve_transparency_alpha(*, enabled: bool, effect_alpha: object = _DEFAULT_EFFECT_ALPHA) -> float:
    return normalize_window_alpha(effect_alpha) if enabled else 1.0


def _window_exists(window: AppearanceWindowProtocol) -> bool:
    try:
        return bool(window.winfo_exists())
    except (AttributeError, TclError):
        return False


def _apply_to_window(window: AppearanceWindowProtocol) -> None:
    if not _window_exists(window):
        return
    dark_theme = _THEME_NAME == 'dark'
    try:
        set_title_bar_color(window, True)
    except (AttributeError, OSError, TclError, TypeError, ValueError):
        return
    try:
        window.configure(background=_DARK_BACKGROUND if dark_theme else _LIGHT_BACKGROUND)
    except (AttributeError, TclError):
        pass
    try:
        window.attributes('-alpha', _WINDOW_ALPHA)
    except (AttributeError, TclError):
        pass


def register_window(window: object) -> None:
    """Register a window once and apply the current theme and transparency."""
    typed_window = cast(AppearanceWindowProtocol, window)
    try:
        _WINDOWS.add(typed_window)
    except TypeError:
        return

    _apply_to_window(typed_window)
    if typed_window in _BOUND_WINDOWS:
        return
    try:
        _BOUND_WINDOWS.add(typed_window)
        typed_window.bind('<Map>', lambda _event: _apply_to_window(typed_window), add='+')
        typed_window.bind('<FocusIn>', lambda _event: _apply_to_window(typed_window), add='+')
        typed_window.after_idle(lambda: _apply_to_window(typed_window))
    except (AttributeError, TclError):
        return


def apply_theme_to_windows(theme_name: str) -> None:
    global _THEME_NAME
    normalized = str(theme_name or '').strip().lower()
    _THEME_NAME = 'dark' if normalized == 'dark' else 'light'
    for window in tuple(_WINDOWS):
        _apply_to_window(window)


def apply_transparency_to_windows(*, enabled: bool, effect_alpha: object = _DEFAULT_EFFECT_ALPHA) -> float:
    global _WINDOW_ALPHA
    _WINDOW_ALPHA = resolve_transparency_alpha(enabled=enabled, effect_alpha=effect_alpha)
    for window in tuple(_WINDOWS):
        _apply_to_window(window)
    return _WINDOW_ALPHA


def current_window_alpha() -> float:
    return _WINDOW_ALPHA


def current_theme_name() -> str:
    return _THEME_NAME


__all__ = [
    'AppearanceWindowProtocol',
    'apply_theme_to_windows',
    'apply_transparency_to_windows',
    'current_theme_name',
    'current_window_alpha',
    'normalize_window_alpha',
    'register_window',
    'resolve_transparency_alpha',
]
