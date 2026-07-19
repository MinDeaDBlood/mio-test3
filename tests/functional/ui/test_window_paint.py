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


import _tkinter

from src.ui.common.window_paint import _geometry_position, paint_window_now


class _RecordingTkEventBoundary:
    def __init__(self) -> None:
        self.flags: list[int] = []
        self.remaining = 3

    def dooneevent(self, flags: int) -> int:
        self.flags.append(flags)
        if self.remaining:
            self.remaining -= 1
            return 1
        return 0


class _MinimalPaintWindow:
    def __init__(self) -> None:
        self.tk = _RecordingTkEventBoundary()
        self.idle_passes = 0

    def update_idletasks(self) -> None:
        self.idle_passes += 1

    def winfo_exists(self) -> int:
        return 1


def test_bounded_first_paint_never_drains_application_timers() -> None:
    window = _MinimalPaintWindow()

    assert paint_window_now(window) is True
    assert window.idle_passes == 2
    assert window.tk.flags
    assert all(flags & _tkinter.WINDOW_EVENTS for flags in window.tk.flags)
    assert all(not flags & _tkinter.TIMER_EVENTS for flags in window.tk.flags)


def test_explicit_geometry_position_wins_over_stale_hidden_window_coordinates() -> None:
    class Window:
        def geometry(self) -> str:
            return "654x389+356+189"

    assert _geometry_position(Window()) == (356, 189)


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
