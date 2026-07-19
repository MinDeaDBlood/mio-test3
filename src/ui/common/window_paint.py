"""Bounded Tk painting that never runs timer or file callbacks."""

from __future__ import annotations

import _tkinter
import os
import re
from tkinter import TclError
from typing import Any


_WINDOW_EVENT_FLAGS = _tkinter.WINDOW_EVENTS | _tkinter.DONT_WAIT
_MAX_FALLBACK_EVENTS = 8

_RDW_INVALIDATE = 0x0001
_RDW_ALLCHILDREN = 0x0080
_RDW_UPDATENOW = 0x0100
_RDW_FRAME = 0x0400
_PM_REMOVE = 0x0001
_GWL_EXSTYLE = -20
_WS_EX_LAYERED = 0x00080000
_LWA_ALPHA = 0x00000002
_DWMWA_CLOAK = 13
_MAX_NATIVE_MESSAGES = 512
_GEOMETRY_RE = re.compile(r'^\d+x\d+([+-]\d+)([+-]\d+)$')


def _geometry_position(window: Any) -> tuple[int, int] | None:
    try:
        match = _GEOMETRY_RE.fullmatch(str(window.geometry()))
        if match is not None:
            return int(match.group(1)), int(match.group(2))
    except (AttributeError, TclError, TypeError, ValueError):
        pass
    return None


def _native_api(window: Any):
    if os.name != 'nt':
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        user32.GetParent.restype = wintypes.HWND
        child_handle = wintypes.HWND(int(window.winfo_id()))
        wrapper_handle = user32.GetParent(child_handle) or child_handle
        return ctypes, wintypes, user32, wrapper_handle
    except (AttributeError, ImportError, OSError, TclError, TypeError, ValueError):
        return None


def set_native_window_alpha(window: Any, alpha: float) -> bool:
    """Apply alpha directly to the real Windows wrapper, even while withdrawn."""
    api = _native_api(window)
    if api is None:
        return False
    _ctypes, _wintypes, user32, wrapper_handle = api
    try:
        get_style = getattr(user32, 'GetWindowLongPtrW', user32.GetWindowLongW)
        set_style = getattr(user32, 'SetWindowLongPtrW', user32.SetWindowLongW)
        style = get_style(wrapper_handle, _GWL_EXSTYLE)
        set_style(wrapper_handle, _GWL_EXSTYLE, style | _WS_EX_LAYERED)
        opacity = max(0, min(255, round(float(alpha) * 255)))
        return bool(
            user32.SetLayeredWindowAttributes(
                wrapper_handle,
                0,
                opacity,
                _LWA_ALPHA,
            )
        )
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def set_native_window_cloaked(window: Any, cloaked: bool) -> bool:
    """Hide or publish a native window through the desktop compositor."""
    api = _native_api(window)
    if api is None:
        return False
    ctypes, _wintypes, _user32, wrapper_handle = api
    try:
        value = ctypes.c_int(1 if cloaked else 0)
        return int(
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wrapper_handle,
                _DWMWA_CLOAK,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        ) == 0
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def stage_window_offscreen(window: Any) -> str | None:
    """Move a withdrawn window off-screen and return its final geometry."""
    if os.name != 'nt':
        return None
    try:
        window.update_idletasks()
        current_width = max(1, int(window.winfo_width()))
        current_height = max(1, int(window.winfo_height()))
        width = max(current_width, int(window.winfo_reqwidth()))
        height = max(current_height, int(window.winfo_reqheight()))
        screen_width = int(window.winfo_screenwidth())
        screen_height = int(window.winfo_screenheight())
        requested_position = _geometry_position(window)
        if width != current_width or height != current_height:
            target_x = max(0, (screen_width - width) // 2)
            target_y = max(0, (screen_height - height) // 2)
        elif requested_position is not None:
            target_x, target_y = requested_position
        else:
            target_x = int(window.winfo_x())
            target_y = int(window.winfo_y())
        target_geometry = f'{width}x{height}{target_x:+d}{target_y:+d}'
        x = screen_width + width + 64
        y = screen_height + height + 64
        window.geometry(f'{width}x{height}+{x}+{y}')
        window.update_idletasks()
        return target_geometry
    except (AttributeError, OSError, TclError, TypeError, ValueError):
        return None


def _pump_native_window_messages(window: Any, max_messages: int) -> bool:
    api = _native_api(window)
    if api is None:
        return False
    ctypes, wintypes, user32, wrapper_handle = api
    try:
        message = wintypes.MSG()
        for _index in range(max(0, min(_MAX_NATIVE_MESSAGES, int(max_messages)))):
            if not user32.PeekMessageW(
                ctypes.byref(message),
                wrapper_handle,
                0,
                0,
                _PM_REMOVE,
            ):
                break
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        return True
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def _redraw_native_window(window: Any) -> bool:
    api = _native_api(window)
    if api is None:
        return False
    _ctypes, _wintypes, user32, wrapper_handle = api
    try:
        return bool(
            user32.RedrawWindow(
                wrapper_handle,
                None,
                None,
                _RDW_INVALIDATE | _RDW_ALLCHILDREN | _RDW_UPDATENOW | _RDW_FRAME,
            )
        )
    except (AttributeError, OSError, TclError, TypeError, ValueError):
        return False


def paint_window_now(
    window: Any,
    *,
    max_tk_events: int = 32,
    max_native_messages: int = _MAX_NATIVE_MESSAGES,
) -> bool:
    """Lay out and paint a window without executing ``after`` callbacks.

    ``update()`` drains every Tcl event class, so opening a window could also
    run scans, timers, modal dialogs and unrelated background work.  Layout
    idles plus native window events are sufficient for a complete first paint
    and keep those application callbacks queued for the normal main loop.
    """
    try:
        window.update_idletasks()
        pumped = (
            _pump_native_window_messages(window, max_native_messages)
            if max_native_messages > 0
            else True
        )
        native_painted = pumped and _redraw_native_window(window)
        do_one_event = window.tk.dooneevent
        event_limit = max(0, int(max_tk_events)) if native_painted else _MAX_FALLBACK_EVENTS
        for _index in range(event_limit):
            if not do_one_event(_WINDOW_EVENT_FLAGS):
                break
        # Tk's WM_PAINT handler records damage and schedules the actual widget
        # drawing as idle work.  Commit that drawing before asking DWM to
        # publish the surface.
        window.update_idletasks()
        if native_painted:
            # RedrawWindow can itself enqueue child Expose/WM_PAINT work.  A
            # final redraw without draining that work exposed classic Canvas,
            # Text and Listbox controls with the Windows class brush for one
            # compositor frame.  Drain only window events once more; timers
            # and file callbacks remain untouched.
            _pump_native_window_messages(window, max_native_messages)
            _redraw_native_window(window)
            for _index in range(event_limit):
                if not do_one_event(_WINDOW_EVENT_FLAGS):
                    break
            window.update_idletasks()
            _pump_native_window_messages(window, max_native_messages)
            return bool(window.winfo_exists())
        return bool(window.winfo_exists())
    except (AttributeError, TclError):
        return False


__all__ = [
    'paint_window_now',
    'set_native_window_alpha',
    'set_native_window_cloaked',
    'stage_window_offscreen',
]
