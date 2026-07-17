"""Atomic redraw control for visible Tk windows.

The context manager prevents Windows from painting intermediate widget and
geometry states while a theme or wizard page is being replaced. Other
platforms expose the same no-op API so callers remain platform independent.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from tkinter import TclError
from typing import Any, Final


if os.name == "nt":
    import ctypes

    _WM_SETREDRAW: Final = 0x000B
    _RDW_INVALIDATE: Final = 0x0001
    _RDW_ERASE: Final = 0x0004
    _RDW_ALLCHILDREN: Final = 0x0080
    _RDW_UPDATENOW: Final = 0x0100
    _RDW_FRAME: Final = 0x0400
    _REDRAW_FLAGS: Final = (
        _RDW_INVALIDATE
        | _RDW_ERASE
        | _RDW_ALLCHILDREN
        | _RDW_UPDATENOW
        | _RDW_FRAME
    )
    _user32: Any = ctypes.windll.user32

    def _window_handle(window: Any) -> int:
        window.update_idletasks()
        widget_handle = int(window.winfo_id())
        parent_handle = int(_user32.GetParent(widget_handle))
        return parent_handle or widget_handle

    @contextmanager
    def suspend_window_redraw(window: Any) -> Iterator[None]:
        """Paint one complete UI state instead of intermediate Windows frames."""

        hwnd = 0
        redraw_disabled = False
        try:
            if bool(window.winfo_exists()):
                hwnd = _window_handle(window)
                _user32.SendMessageW(hwnd, _WM_SETREDRAW, 0, 0)
                redraw_disabled = True
        except (AttributeError, OSError, TclError, TypeError, ValueError):
            hwnd = 0
            redraw_disabled = False

        try:
            yield
        finally:
            if redraw_disabled and hwnd:
                try:
                    _user32.SendMessageW(hwnd, _WM_SETREDRAW, 1, 0)
                    _user32.RedrawWindow(
                        hwnd,
                        None,
                        None,
                        _REDRAW_FLAGS,
                    )
                except (AttributeError, OSError, TypeError, ValueError):
                    pass
else:

    @contextmanager
    def suspend_window_redraw(window: Any) -> Iterator[None]:
        del window
        yield


__all__ = ["suspend_window_redraw"]
