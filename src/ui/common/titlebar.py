"""Windows non-client frame styling for Tk windows.

The application keeps native dragging, resizing, snapping, minimizing and taskbar
behaviour, but owns the visual palette of the caption and border.  DWM support
varies by Windows release, so every attribute is applied independently and older
systems gracefully fall back to immersive dark mode.
"""

from __future__ import annotations

import os
from tkinter import TclError
from typing import Final, Protocol, cast

_DARK_MODE_ATTRIBUTE: Final = 20
_DARK_MODE_ATTRIBUTE_LEGACY: Final = 19
_BORDER_COLOR_ATTRIBUTE: Final = 34
_CAPTION_COLOR_ATTRIBUTE: Final = 35
_TEXT_COLOR_ATTRIBUTE: Final = 36
_COLOR_DEFAULT: Final = 0xFFFFFFFF
_COLOR_MIO_BLACK: Final = 0x00101010
_COLOR_WHITE: Final = 0x00FFFFFF


class TitlebarWindowProtocol(Protocol):
    def update_idletasks(self) -> object: ...
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
        window.update_idletasks()
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

    def _set_dwm_color(hwnd: int, attribute: int, value: int) -> bool:
        data = ctypes.c_uint(value)
        result = _windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            attribute,
            ctypes.byref(data),
            ctypes.sizeof(data),
        )
        return int(result) == 0

    def set_title_bar_color(window: TitlebarWindowProtocol, dark_value: int | bool = True) -> None:
        """Apply the MIO black caption, border and readable caption text.

        A native frame is retained intentionally because it is the only reliable
        way to preserve Windows resize zones, snap layouts, taskbar behaviour and
        accessibility without duplicating the window manager in Tk code.
        """
        try:
            hwnd = _window_handle(window)
            dark_enabled = bool(dark_value)
            mode_value = 1 if dark_enabled else 0
            if not _set_dwm_int(hwnd, _DARK_MODE_ATTRIBUTE, mode_value):
                _set_dwm_int(hwnd, _DARK_MODE_ATTRIBUTE_LEGACY, mode_value)

            if dark_enabled:
                _set_dwm_color(hwnd, _BORDER_COLOR_ATTRIBUTE, _COLOR_MIO_BLACK)
                _set_dwm_color(hwnd, _CAPTION_COLOR_ATTRIBUTE, _COLOR_MIO_BLACK)
                _set_dwm_color(hwnd, _TEXT_COLOR_ATTRIBUTE, _COLOR_WHITE)
            else:
                _set_dwm_color(hwnd, _BORDER_COLOR_ATTRIBUTE, _COLOR_DEFAULT)
                _set_dwm_color(hwnd, _CAPTION_COLOR_ATTRIBUTE, _COLOR_DEFAULT)
                _set_dwm_color(hwnd, _TEXT_COLOR_ATTRIBUTE, _COLOR_DEFAULT)
            window.update_idletasks()
        except (AttributeError, OSError, TclError, TypeError, ValueError):
            return
else:

    def set_title_bar_color(window: TitlebarWindowProtocol, dark_value: int | bool = True) -> None:
        del window, dark_value


__all__ = ['TitlebarWindowProtocol', 'set_title_bar_color']
