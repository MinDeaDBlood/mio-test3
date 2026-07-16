from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, overload


@dataclass(frozen=True)
class WelcomePageLayout:
    min_width: int
    min_height: int
    preferred_width: int
    preferred_height: int


@dataclass(frozen=True)
class WelcomeWindowSize:
    width: int
    height: int
    min_width: int
    min_height: int
    x: int
    y: int


WELCOME_PAGE_LAYOUTS: tuple[WelcomePageLayout, ...] = (
    WelcomePageLayout(min_width=480, min_height=280, preferred_width=580, preferred_height=320),
    WelcomePageLayout(min_width=300, min_height=240, preferred_width=360, preferred_height=280),
    WelcomePageLayout(min_width=360, min_height=260, preferred_width=460, preferred_height=300),
    WelcomePageLayout(min_width=640, min_height=360, preferred_width=1000, preferred_height=470),
    WelcomePageLayout(min_width=640, min_height=360, preferred_width=1000, preferred_height=470),
    WelcomePageLayout(min_width=520, min_height=280, preferred_width=660, preferred_height=340),
)


class WelcomeWindowProtocol(Protocol):
    def update_idletasks(self) -> object: ...
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


class WelcomeContentProtocol(Protocol):
    def update_idletasks(self) -> object: ...
    def winfo_reqwidth(self) -> int: ...
    def winfo_reqheight(self) -> int: ...


def get_page_layout(step: int) -> WelcomePageLayout:
    if not isinstance(step, int):
        raise TypeError('Welcome page step must be an integer.')
    if step < 0 or step >= len(WELCOME_PAGE_LAYOUTS):
        raise ValueError(f'Unsupported welcome page step: {step}')
    return WELCOME_PAGE_LAYOUTS[step]


def _available_size(*, screen_width: int, screen_height: int, screen_margin: int) -> tuple[int, int]:
    if screen_width <= 0 or screen_height <= 0:
        raise ValueError('Screen size must be greater than zero.')
    if screen_margin < 0:
        raise ValueError('Screen margin cannot be negative.')
    return (
        max(screen_width - (screen_margin * 2), 1),
        max(screen_height - (screen_margin * 2), 1),
    )


def compute_welcome_window_size(
    *,
    requested_width: int,
    requested_height: int,
    screen_width: int,
    screen_height: int,
    layout: WelcomePageLayout,
    horizontal_padding: int = 16,
    vertical_padding: int = 16,
    screen_margin: int = 32,
) -> WelcomeWindowSize:
    if requested_width <= 0 or requested_height <= 0:
        raise ValueError('Requested welcome size must be greater than zero.')
    if horizontal_padding < 0 or vertical_padding < 0:
        raise ValueError('Welcome padding cannot be negative.')

    available_width, available_height = _available_size(
        screen_width=screen_width,
        screen_height=screen_height,
        screen_margin=screen_margin,
    )
    target_width = max(requested_width + horizontal_padding, layout.preferred_width)
    target_height = max(requested_height + vertical_padding, layout.preferred_height)
    width = min(target_width, available_width)
    height = min(target_height, available_height)
    min_width = min(layout.min_width, available_width)
    min_height = min(layout.min_height, available_height)
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    return WelcomeWindowSize(
        width=width,
        height=height,
        min_width=min_width,
        min_height=min_height,
        x=x,
        y=y,
    )


def compute_content_wrap_width(
    *,
    screen_width: int,
    layout: WelcomePageLayout,
    screen_margin: int = 32,
    horizontal_chrome: int = 64,
    minimum: int = 220,
) -> int:
    if horizontal_chrome < 0 or minimum <= 0:
        raise ValueError('Welcome content width settings are invalid.')
    available_width, _ = _available_size(
        screen_width=screen_width,
        screen_height=1,
        screen_margin=screen_margin,
    )
    window_width = min(layout.preferred_width, available_width)
    return max(window_width - horizontal_chrome, minimum)


def fit_welcome_window(
    main_window: WelcomeWindowProtocol,
    content: WelcomeContentProtocol,
    *,
    layout: WelcomePageLayout,
) -> WelcomeWindowSize:
    content.update_idletasks()
    size = compute_welcome_window_size(
        requested_width=content.winfo_reqwidth(),
        requested_height=content.winfo_reqheight(),
        screen_width=main_window.winfo_screenwidth(),
        screen_height=main_window.winfo_screenheight(),
        layout=layout,
    )
    main_window.resizable(True, True)
    main_window.minsize(size.min_width, size.min_height)
    main_window.geometry(f'{size.width}x{size.height}+{size.x}+{size.y}')
    main_window.update_idletasks()
    return size


def release_welcome_window(main_window: WelcomeWindowProtocol) -> None:
    main_window.minsize(1, 1)
    main_window.update_idletasks()


__all__ = [
    'WELCOME_PAGE_LAYOUTS',
    'WelcomeContentProtocol',
    'WelcomePageLayout',
    'WelcomeWindowProtocol',
    'WelcomeWindowSize',
    'compute_content_wrap_width',
    'compute_welcome_window_size',
    'fit_welcome_window',
    'get_page_layout',
    'release_welcome_window',
]
