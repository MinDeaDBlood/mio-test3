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


from src.ui.window_sections.main_window_layout import MainWindowSize, compute_main_window_size


def test_main_window_uses_requested_content_size_when_it_fits() -> None:
    size = compute_main_window_size(
        requested_width=1284,
        requested_height=586,
        screen_width=1920,
        screen_height=1080,
    )
    assert size == MainWindowSize(
        width=1284,
        height=600,
        min_width=960,
        min_height=600,
        x=(1920 - 1284) // 2,
        y=(1080 - 600) // 2,
    )


def test_main_window_does_not_keep_smaller_welcome_geometry() -> None:
    size = compute_main_window_size(
        requested_width=1284,
        requested_height=586,
        screen_width=1366,
        screen_height=768,
    )
    assert size.width == 1284
    assert size.height == 600
    assert size.width > 1000
    assert size.height > 470


def test_main_window_is_clamped_to_small_screen() -> None:
    size = compute_main_window_size(
        requested_width=1284,
        requested_height=586,
        screen_width=1024,
        screen_height=600,
    )
    assert size.width == 976
    assert size.height == 552
    assert size.min_width == 960
    assert size.min_height == 552
    assert size.x == 24
    assert size.y == 24

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
