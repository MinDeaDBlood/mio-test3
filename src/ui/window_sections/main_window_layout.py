from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, overload


@dataclass(frozen=True)
class MainWindowSize:
    width: int
    height: int
    min_width: int
    min_height: int
    x: int
    y: int


class MainWindowLayoutPort(Protocol):
    def update_idletasks(self) -> object: ...
    def winfo_reqwidth(self) -> int: ...
    def winfo_reqheight(self) -> int: ...
    def winfo_screenwidth(self) -> int: ...
    def winfo_screenheight(self) -> int: ...
    @overload
    def geometry(self, geometry: None = None) -> str: ...
    @overload
    def geometry(self, geometry: str) -> None: ...
    @overload
    def minsize(self, width: None = None, height: None = None) -> tuple[int, int]: ...
    @overload
    def minsize(self, width: int, height: int) -> None: ...
    @overload
    def resizable(self, width: None = None, height: None = None) -> tuple[bool, bool]: ...
    @overload
    def resizable(self, width: bool, height: bool) -> None: ...


def compute_main_window_size(
    *,
    requested_width: int,
    requested_height: int,
    screen_width: int,
    screen_height: int,
    min_width: int = 960,
    min_height: int = 600,
    screen_margin: int = 24,
) -> MainWindowSize:
    if requested_width <= 0 or requested_height <= 0:
        raise ValueError('Requested main window size must be greater than zero.')
    if screen_width <= 0 or screen_height <= 0:
        raise ValueError('Screen size must be greater than zero.')
    if min_width <= 0 or min_height <= 0:
        raise ValueError('Minimum main window size must be greater than zero.')
    if screen_margin < 0:
        raise ValueError('Screen margin cannot be negative.')

    available_width = max(screen_width - (screen_margin * 2), 1)
    available_height = max(screen_height - (screen_margin * 2), 1)
    width = min(max(requested_width, min_width), available_width)
    height = min(max(requested_height, min_height), available_height)
    effective_min_width = min(min_width, available_width)
    effective_min_height = min(min_height, available_height)
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    return MainWindowSize(
        width=width,
        height=height,
        min_width=effective_min_width,
        min_height=effective_min_height,
        x=x,
        y=y,
    )


def fit_main_window_to_content(window: MainWindowLayoutPort) -> MainWindowSize:
    window.update_idletasks()
    size = compute_main_window_size(
        requested_width=window.winfo_reqwidth(),
        requested_height=window.winfo_reqheight(),
        screen_width=window.winfo_screenwidth(),
        screen_height=window.winfo_screenheight(),
    )
    window.resizable(True, True)
    window.minsize(size.min_width, size.min_height)
    window.geometry(f'{size.width}x{size.height}+{size.x}+{size.y}')
    window.update_idletasks()
    return size


__all__ = [
    'MainWindowLayoutPort',
    'MainWindowSize',
    'compute_main_window_size',
    'fit_main_window_to_content',
]
