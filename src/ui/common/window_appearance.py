"""Shared appearance state for every root and Toplevel window."""

from __future__ import annotations

from tkinter import TclError
from collections.abc import Callable
from typing import Any, Protocol, cast
from weakref import WeakSet

from src.ui.common.themes.identifiers import DARK_THEME, require_theme_id
from src.ui.common.themes.native_palette import apply_native_theme, get_theme_palette
from src.ui.common.titlebar import TitlebarWindowProtocol, set_title_bar_color



class AppearanceWindowProtocol(TitlebarWindowProtocol, Protocol):
    def winfo_exists(self) -> int: ...
    def attributes(self, *args: object) -> object: ...
    def configure(self, **kwargs: object) -> object: ...
    def bind(self, sequence: str, func: Callable[[object], object], add: str | None = None) -> object: ...
    def after_idle(self, func: Callable[[], object]) -> object: ...


_WINDOWS: WeakSet[AppearanceWindowProtocol] = WeakSet()
_BOUND_WINDOWS: WeakSet[AppearanceWindowProtocol] = WeakSet()
_THEME_REAPPLY_PENDING: WeakSet[AppearanceWindowProtocol] = WeakSet()
_THEME_ID = DARK_THEME
_WINDOW_ALPHA = 1.0
_MIN_ALPHA = 0.55
_MAX_ALPHA = 1.0
_DEFAULT_EFFECT_ALPHA = 0.90


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


def _apply_to_window(
    window: AppearanceWindowProtocol,
    *,
    include_widget_tree: bool = True,
) -> None:
    if not _window_exists(window):
        return
    palette = get_theme_palette(_THEME_ID)
    try:
        set_title_bar_color(window, True)
    except (AttributeError, OSError, TclError, TypeError, ValueError):
        pass
    try:
        window.configure(background=palette.window_background)
    except (AttributeError, TclError):
        pass
    try:
        window.attributes('-alpha', _WINDOW_ALPHA)
    except (AttributeError, TclError):
        pass
    if include_widget_tree:
        try:
            apply_native_theme(window, _THEME_ID)
        except (AttributeError, TclError, TypeError):
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
        def apply_after_map(event: Any) -> None:
            if event.widget is typed_window:
                _apply_to_window(typed_window)

        typed_window.bind('<Map>', apply_after_map, add='+')
        typed_window.bind(
            '<FocusIn>',
            lambda _event: _apply_to_window(typed_window, include_widget_tree=False),
            add='+',
        )
        typed_window.after_idle(lambda: _apply_to_window(typed_window))
    except (AttributeError, TclError):
        return


def _reapply_theme_after_ttk(window: AppearanceWindowProtocol) -> None:
    try:
        _THEME_REAPPLY_PENDING.discard(window)
    except TypeError:
        return
    _apply_to_window(window)


def _schedule_theme_reapply(window: AppearanceWindowProtocol) -> None:
    if window in _THEME_REAPPLY_PENDING:
        return
    try:
        _THEME_REAPPLY_PENDING.add(window)
        window.after_idle(lambda: _reapply_theme_after_ttk(window))
    except (AttributeError, TclError, TypeError):
        _THEME_REAPPLY_PENDING.discard(window)


def apply_theme_to_windows(theme_id: str) -> None:
    global _THEME_ID
    _THEME_ID = require_theme_id(theme_id)
    for window in tuple(_WINDOWS):
        _apply_to_window(window)
        _schedule_theme_reapply(window)


def apply_transparency_to_windows(*, enabled: bool, effect_alpha: object = _DEFAULT_EFFECT_ALPHA) -> float:
    global _WINDOW_ALPHA
    _WINDOW_ALPHA = resolve_transparency_alpha(enabled=enabled, effect_alpha=effect_alpha)
    for window in tuple(_WINDOWS):
        _apply_to_window(window)
    return _WINDOW_ALPHA


def current_window_alpha() -> float:
    return _WINDOW_ALPHA


def current_theme_id() -> str:
    return _THEME_ID


__all__ = [
    'AppearanceWindowProtocol',
    'apply_theme_to_windows',
    'apply_transparency_to_windows',
    'current_theme_id',
    'current_window_alpha',
    'normalize_window_alpha',
    'register_window',
    'resolve_transparency_alpha',
]
