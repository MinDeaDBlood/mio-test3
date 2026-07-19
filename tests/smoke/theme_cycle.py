from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / 'src').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'tests').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'scripts').is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f'Project root was not found for {__file__}')

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ''}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix('')
    __package__ = '.'.join(_direct_relative.parts[:-1])

import tkinter as tk
from tkinter import ttk

from src.ui.common.themes.native_palette import get_theme_palette
from src.ui.common.window_appearance import current_window_alpha
from src.ui.common.window_reveal import reveal_window_after_layout
from src.ui.welcome.wizard import Welcome
from tests.smoke.welcome import _Controller, _TestWelcome
from tests.support.runtime_smoke import lang, prepare_root
from tests.support.theme_assertions import assert_dark_theme_applied, cycle_light_dark


class _Actions:
    def choose_workdir(self) -> str:
        return ''

    def open_workdir(self, _path: str) -> None:
        return None

    def apply_language(self, _language_name: str) -> None:
        return None

    def set_oobe_active(self, _active: bool) -> None:
        return None


root = prepare_root()
reveal_window_after_layout(root, target_alpha=current_window_alpha(), focus=True)

classic_text = tk.Text(root)
classic_text.pack()
classic_list = tk.Listbox(root)
classic_list.pack()
combobox = ttk.Combobox(root, values=('English', 'Russian'), state='readonly')
combobox.pack()
root.update()

layout_before = (
    root.geometry(),
    root.sub_win2.winfo_x(),
    root.sub_win2.winfo_width(),
    root.sub_win3.winfo_x(),
    root.sub_win3.winfo_width(),
)

cycle_light_dark(root, root)
layout_after = (
    root.geometry(),
    root.sub_win2.winfo_x(),
    root.sub_win2.winfo_width(),
    root.sub_win3.winfo_x(),
    root.sub_win3.winfo_width(),
)
assert layout_after == layout_before
assert classic_text.cget('background') == get_theme_palette('dark').input_background
assert classic_list.cget('background') == get_theme_palette('dark').input_background

child_window = tk.Toplevel(root)
child_entry = ttk.Entry(child_window)
child_entry.pack()
child_window.update_idletasks()
child_window.focus_force()
child_entry.focus_set()
root.update()
assert root.focus_get() is child_entry
cycle_light_dark(root, root)
assert root.focus_get() is child_entry
child_window.destroy()

welcome: Welcome = _TestWelcome(
    main_window=root,
    controller=_Controller(),
    language_var=tk.StringVar(master=root, value='English'),
    actions=_Actions(),
    texts=lang,
)
stable_pages = dict(welcome._page_frames)
stable_geometry = root.geometry()
assert len(stable_pages) == 6
assert all(frame.winfo_manager() == 'grid' for frame in stable_pages.values())

for step in range(6):
    welcome.change_page(step)
    root.update_idletasks()
    root.update()
    assert welcome.frame is stable_pages[step]
    assert all(frame.winfo_exists() for frame in stable_pages.values())
    assert all(frame.winfo_manager() == 'grid' for frame in stable_pages.values())
    assert root.geometry() == stable_geometry
    assert_dark_theme_applied(welcome)

welcome.change_page(0)
root.update_idletasks()
root.update()
size_before_move = (root.winfo_width(), root.winfo_height())
root.geometry('+120+140')
root.update_idletasks()
root.update()
assert (root.winfo_width(), root.winfo_height()) == size_before_move

geometry_before_language_refresh = root.geometry()
pages_before_language_refresh = dict(welcome._page_frames)
welcome.apply_selected_language()
root.update_idletasks()
root.update()
assert welcome.frame is welcome._page_frames[welcome.oobe]
assert all(not frame.winfo_exists() for frame in pages_before_language_refresh.values())
assert all(frame.winfo_exists() for frame in welcome._page_frames.values())
assert all(frame.winfo_manager() == 'grid' for frame in welcome._page_frames.values())
assert root.geometry() == geometry_before_language_refresh
assert_dark_theme_applied(welcome)

welcome.destroy_welcome()
root.destroy()
print('THEME_CYCLE_SMOKE_OK')

if __name__ == '__main__':
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
