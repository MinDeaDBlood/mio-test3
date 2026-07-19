"""Native Windows non-client frame theming for Tk windows."""

from __future__ import annotations

import os
from tkinter import TclError
from typing import Final, Protocol, cast

_DARK_MODE_ATTRIBUTE: Final = 20
_DARK_MODE_ATTRIBUTE_LEGACY: Final = 19


class TitlebarWindowProtocol(Protocol):
    def winfo_id(self) -> int: ...


if os.name == 'nt':
    import ctypes

    class _DwmApiProtocol(Protocol):
        def DwmSetWindowAttribute(self, hwnd: int, attribute: int, data: object, size: int) -> int: ...

    class _User32Protocol(Protocol):
        def GetParent(self, hwnd: int) -> int: ...

    class _WindllProtocol(Protocol):
        dwmapi: _DwmApiProtocol
        user32: _User32Protocol

    _windll = cast(_WindllProtocol, getattr(ctypes, 'windll'))

    def _window_handle(window: TitlebarWindowProtocol) -> int:
        widget_handle = int(window.winfo_id())
        parent_handle = int(_windll.user32.GetParent(widget_handle))
        return parent_handle or widget_handle

    def _set_dwm_int(hwnd: int, attribute: int, value: int) -> bool:
        data = ctypes.c_int(value)
        result = _windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            attribute,
            ctypes.byref(data),
            ctypes.sizeof(data),
        )
        return int(result) == 0

    def set_title_bar_color(window: TitlebarWindowProtocol, dark_value: int | bool = True) -> None:
        """Let Windows draw the complete frame using its immersive theme."""
        try:
            hwnd = _window_handle(window)
            dark_enabled = bool(dark_value)
            mode_value = 1 if dark_enabled else 0
            if not _set_dwm_int(hwnd, _DARK_MODE_ATTRIBUTE, mode_value):
                _set_dwm_int(hwnd, _DARK_MODE_ATTRIBUTE_LEGACY, mode_value)
        except (AttributeError, OSError, TclError, TypeError, ValueError):
            return
else:

    def set_title_bar_color(window: TitlebarWindowProtocol, dark_value: int | bool = True) -> None:
        del window, dark_value


__all__ = ['TitlebarWindowProtocol', 'set_title_bar_color']
