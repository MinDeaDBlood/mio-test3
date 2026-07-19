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


from pathlib import Path
import sys

sys.path.insert(0, '.')

from src.ui.common.geometry import move_center


class FakeWindow:
    def __init__(self, *, screen_width=1920, screen_height=1080, width=800, height=600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = width
        self.height = height
        self.settled = False
        self.events: list[str] = []
        self.last_geometry = ''

    def update_idletasks(self):
        self.events.append('update_idletasks')
        self.settled = True

    def winfo_width(self):
        self.events.append('winfo_width')
        return self.width if self.settled else 1

    def winfo_height(self):
        self.events.append('winfo_height')
        return self.height if self.settled else 1

    def winfo_reqwidth(self):
        self.events.append('winfo_reqwidth')
        return self.width if self.settled else 1

    def winfo_reqheight(self):
        self.events.append('winfo_reqheight')
        return self.height if self.settled else 1

    def winfo_screenwidth(self):
        return self.screen_width

    def winfo_screenheight(self):
        return self.screen_height

    def geometry(self, value):
        self.events.append(f'geometry:{value}')
        self.last_geometry = value


def test_move_center_waits_for_settled_geometry_before_positioning() -> None:
    window = FakeWindow(width=800, height=600)

    move_center(window)

    assert window.events[0] == 'update_idletasks'
    assert window.last_geometry == '+560+240'


def test_move_center_clamps_position_when_window_is_larger_than_screen() -> None:
    window = FakeWindow(screen_width=800, screen_height=600, width=1200, height=900)

    move_center(window)

    assert window.last_geometry == '+0+0'


def test_pack_super_centers_after_final_widgets_are_built() -> None:
    source = Path('src/ui/tabs/project/pack/super/window.py').read_text(encoding='utf-8')

    assert source.count('self.center_on_screen(force=True)') == 1
    assert 'self._repaint_after_move = True' in source
    center = source.index('self.center_on_screen(force=True)')
    reveal = source.index('self.deiconify()', center)
    load = source.index('controller.request_initial_data(', reveal)
    assert center < reveal < load

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
