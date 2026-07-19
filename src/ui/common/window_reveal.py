"""First-frame reveal for prepared Tk roots."""

from __future__ import annotations

import os
from tkinter import TclError
from typing import Any

from src.ui.common.window_appearance import current_window_alpha
from src.ui.common.window_paint import (
    paint_window_now,
    set_native_window_alpha,
    stage_window_offscreen,
)
from src.ui.common.titlebar import set_title_bar_color


def _window_exists(window: Any) -> bool:
    try:
        return bool(window.winfo_exists())
    except (AttributeError, TclError):
        return False


def _restore_alpha_gate(window: Any, generation: int, fallback: float) -> None:
    if getattr(window, '_mio_reveal_generation', None) != generation:
        return
    if _window_exists(window):
        try:
            target_alpha = current_window_alpha()
            window.attributes('-alpha', target_alpha)
            set_native_window_alpha(window, target_alpha)
        except (AttributeError, TclError, TypeError, ValueError):
            try:
                window.attributes('-alpha', fallback)
            except (AttributeError, TclError, TypeError, ValueError):
                pass
    try:
        setattr(window, '_appearance_alpha_gated', False)
    except (AttributeError, TclError):
        pass


def reveal_window_after_layout(
    window: Any,
    *,
    target_alpha: float,
    focus: bool = True,
) -> None:
    """Map a prepared root while its first native paint remains transparent."""
    generation = int(getattr(window, '_mio_reveal_generation', 0)) + 1
    setattr(window, '_mio_reveal_generation', generation)
    target_geometry = stage_window_offscreen(window)
    gated = False
    if os.name == 'nt':
        try:
            window.attributes('-alpha', 0.0)
            set_native_window_alpha(window, 0.0)
            set_title_bar_color(window, True)
            setattr(window, '_appearance_alpha_gated', True)
            gated = True
        except (AttributeError, TclError):
            pass

    try:
        window.deiconify()
        if gated:
            set_native_window_alpha(window, 0.0)
        set_title_bar_color(window, True)
        # Idle layout alone does not drain the native Map/Expose/WM_PAINT
        # queue on Windows.  Keep the root transparent through one complete
        # event pass so no unpainted class-brush fragments can become visible.
        if not paint_window_now(window, max_tk_events=48):
            if gated:
                _restore_alpha_gate(window, generation, target_alpha)
            return
        if target_geometry is not None:
            window.geometry(target_geometry)
            if gated:
                set_native_window_alpha(window, 0.0)
            set_title_bar_color(window, True)
            # The hidden surface was already painted at this exact size.  A
            # position-only move can reuse it and avoids a second synchronous
            # redraw on the UI thread.
            window.update_idletasks()
        window.lift()
        if focus:
            try:
                window.focus_force()
            except (AttributeError, TclError):
                window.focus_set()
    except (AttributeError, TclError):
        if gated:
            _restore_alpha_gate(window, generation, target_alpha)
        return
    if not _window_exists(window):
        if gated:
            _restore_alpha_gate(window, generation, target_alpha)
        return
    if getattr(window, '_mio_reveal_generation', None) != generation:
        return

    if not gated:
        return

    def finish_reveal() -> None:
        if getattr(window, '_mio_reveal_generation', None) != generation:
            return
        try:
            import ctypes

            if _window_exists(window):
                ctypes.windll.dwmapi.DwmFlush()
        except (AttributeError, OSError, TclError, TypeError, ValueError):
            pass
        finally:
            _restore_alpha_gate(window, generation, target_alpha)

    finish_reveal()


__all__ = ['reveal_window_after_layout']
