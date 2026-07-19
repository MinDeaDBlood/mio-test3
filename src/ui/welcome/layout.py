from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, overload


@dataclass(frozen=True)
class WelcomeWindowSize:
    width: int
    height: int
    min_width: int
    min_height: int
    x: int
    y: int


class WelcomeWindowProtocol(Protocol):
    def update_idletasks(self) -> object: ...
    def winfo_screenwidth(self) -> int: ...
    def winfo_screenheight(self) -> int: ...
    def winfo_reqwidth(self) -> int: ...
    def winfo_reqheight(self) -> int: ...

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


class WelcomeContentProtocol(Protocol):
    def update_idletasks(self) -> object: ...
    def winfo_reqwidth(self) -> int: ...
    def winfo_reqheight(self) -> int: ...


def compute_welcome_window_size(
    *,
    requested_width: int,
    requested_height: int,
    screen_width: int,
    screen_height: int,
    screen_margin: int = 32,
) -> WelcomeWindowSize:
    """Use the page's natural Tk size, matching the original wizard."""

    if requested_width <= 0 or requested_height <= 0:
        raise ValueError('Requested welcome size must be greater than zero.')
    if screen_width <= 0 or screen_height <= 0:
        raise ValueError('Screen size must be greater than zero.')
    if screen_margin < 0:
        raise ValueError('Screen margin cannot be negative.')

    available_width = max(screen_width - (screen_margin * 2), 1)
    available_height = max(screen_height - (screen_margin * 2), 1)
    width = min(requested_width, available_width)
    height = min(requested_height, available_height)
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    return WelcomeWindowSize(
        width=width,
        height=height,
        min_width=width,
        min_height=height,
        x=x,
        y=y,
    )


def fit_welcome_window(
    main_window: WelcomeWindowProtocol,
    content: WelcomeContentProtocol,
) -> WelcomeWindowSize:
    """Measure the ready page and apply one final native geometry change."""

    content.update_idletasks()
    requested_width = max(content.winfo_reqwidth(), main_window.winfo_reqwidth())
    requested_height = max(content.winfo_reqheight(), main_window.winfo_reqheight())
    size = compute_welcome_window_size(
        requested_width=requested_width,
        requested_height=requested_height,
        screen_width=main_window.winfo_screenwidth(),
        screen_height=main_window.winfo_screenheight(),
    )
    main_window.resizable(True, True)
    main_window.minsize(size.min_width, size.min_height)
    main_window.geometry(f'{size.width}x{size.height}+{size.x}+{size.y}')
    return size


def release_welcome_window(main_window: WelcomeWindowProtocol) -> None:
    main_window.minsize(1, 1)


__all__ = [
    'WelcomeContentProtocol',
    'WelcomeWindowProtocol',
    'WelcomeWindowSize',
    'compute_welcome_window_size',
    'fit_welcome_window',
    'release_welcome_window',
]
