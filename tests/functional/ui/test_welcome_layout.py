from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


from src.ui.welcome.layout import (
    WelcomeWindowSize,
    compute_welcome_window_size,
    fit_welcome_window,
    release_welcome_window,
)
from src.ui.welcome.wizard import Welcome


class _FakeWelcomeWindow:
    def __init__(self) -> None:
        self.events: list[tuple[object, ...]] = []

    def update_idletasks(self) -> None:
        self.events.append(('update_idletasks',))

    def winfo_reqwidth(self) -> int:
        return 420

    def winfo_reqheight(self) -> int:
        return 260

    def winfo_screenwidth(self) -> int:
        return 1920

    def winfo_screenheight(self) -> int:
        return 1080

    def geometry(self, value: str) -> None:
        self.events.append(('geometry', value))

    def minsize(self, width: int, height: int) -> None:
        self.events.append(('minsize', width, height))

    def resizable(self, width: bool, height: bool) -> None:
        self.events.append(('resizable', width, height))


class _FakeWelcomeContent:
    def __init__(self) -> None:
        self.update_count = 0

    def update_idletasks(self) -> None:
        self.update_count += 1

    def winfo_reqwidth(self) -> int:
        return 580

    def winfo_reqheight(self) -> int:
        return 320


class _FakeFocusWidget:
    def __init__(
        self,
        path: str,
        *,
        takefocus: object = 'ttk::takefocus',
        children: tuple['_FakeFocusWidget', ...] = (),
    ) -> None:
        self.path = path
        self.takefocus = takefocus
        self.children = children

    def __str__(self) -> str:
        return self.path

    def winfo_children(self) -> tuple['_FakeFocusWidget', ...]:
        return self.children

    def cget(self, option: str) -> object:
        assert option == 'takefocus'
        return self.takefocus

    def configure(self, *, takefocus: object) -> None:
        self.takefocus = takefocus


def test_compute_welcome_window_size_uses_natural_page_size() -> None:
    size = compute_welcome_window_size(
        requested_width=580,
        requested_height=320,
        screen_width=1920,
        screen_height=1080,
    )
    assert size == WelcomeWindowSize(
        width=580,
        height=320,
        min_width=580,
        min_height=320,
        x=(1920 - 580) // 2,
        y=(1080 - 320) // 2,
    )


def test_compute_welcome_window_size_does_not_add_hidden_padding() -> None:
    size = compute_welcome_window_size(
        requested_width=421,
        requested_height=277,
        screen_width=1920,
        screen_height=1080,
    )
    assert size.width == 421
    assert size.height == 277
    assert size.min_width == 421
    assert size.min_height == 277


def test_compute_welcome_window_size_is_clamped_to_small_screen() -> None:
    size = compute_welcome_window_size(
        requested_width=1900,
        requested_height=1200,
        screen_width=480,
        screen_height=320,
    )
    assert size.width == 416
    assert size.height == 256
    assert size.min_width == 416
    assert size.min_height == 256
    assert size.x == 32
    assert size.y == 32


def test_invalid_welcome_dimensions_are_rejected() -> None:
    try:
        compute_welcome_window_size(
            requested_width=0,
            requested_height=100,
            screen_width=1920,
            screen_height=1080,
        )
    except ValueError as exc:
        assert str(exc) == 'Requested welcome size must be greater than zero.'
    else:
        raise AssertionError('Invalid welcome dimensions were accepted.')


def test_fit_welcome_window_uses_one_final_geometry_without_root_flush() -> None:
    window = _FakeWelcomeWindow()
    content = _FakeWelcomeContent()

    size = fit_welcome_window(window, content)

    assert content.update_count == 1
    assert window.events == [
        ('resizable', True, True),
        ('minsize', 580, 320),
        ('geometry', f'580x320+{size.x}+{size.y}'),
    ]


def test_release_welcome_window_does_not_flush_empty_root() -> None:
    window = _FakeWelcomeWindow()

    release_welcome_window(window)

    assert window.events == [('minsize', 1, 1)]


def test_cached_wizard_pages_only_enable_focus_on_active_page() -> None:
    first_control = _FakeFocusWidget('.page0.control')
    second_control = _FakeFocusWidget('.page1.control', takefocus=True)
    first_page = _FakeFocusWidget('.page0', children=(first_control,))
    second_page = _FakeFocusWidget('.page1', children=(second_control,))
    view = object.__new__(Welcome)
    view._page_frames = {0: first_page, 1: second_page}
    view._page_takefocus = {}

    view._set_active_page_focusability(0)

    assert first_control.takefocus == 'ttk::takefocus'
    assert second_control.takefocus is False

    view._set_active_page_focusability(1)

    assert first_control.takefocus is False
    assert second_control.takefocus is True


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
