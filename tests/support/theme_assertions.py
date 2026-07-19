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
from tkinter import TclError, ttk

import sv_ttk

from src.ui.common.themes.native_palette import get_theme_palette
from src.ui.common.window_appearance import apply_theme_to_windows


_CLASSIC_BACKGROUND_CLASSES = {
    'Button',
    'Canvas',
    'Checkbutton',
    'Entry',
    'Frame',
    'Label',
    'Labelframe',
    'Listbox',
    'Menu',
    'Radiobutton',
    'Scale',
    'Scrollbar',
    'Spinbox',
    'Text',
}


def _walk(widget: tk.Misc) -> tuple[tk.Misc, ...]:
    result: list[tk.Misc] = []
    stack: list[tk.Misc] = [widget]
    while stack:
        current = stack.pop()
        result.append(current)
        try:
            stack.extend(reversed(current.winfo_children()))
        except TclError:
            continue
    return tuple(result)


def _combobox_popdown_background(widget: ttk.Combobox) -> str:
    popdown = str(widget.tk.call('ttk::combobox::PopdownWindow', widget._w))
    return str(widget.tk.call(f'{popdown}.f.l', 'cget', '-background'))


def assert_dark_theme_applied(widget: tk.Misc) -> None:
    dark = get_theme_palette('dark')
    light = get_theme_palette('light')
    light_backgrounds = {
        light.window_background.lower(),
        light.surface_background.lower(),
        light.input_background.lower(),
        light.active_background.lower(),
    }
    for current in _walk(widget):
        if isinstance(current, ttk.Combobox):
            assert _combobox_popdown_background(current).lower() == dark.input_background.lower()
            continue
        try:
            widget_class = str(current.winfo_class())
        except TclError:
            continue
        if widget_class not in _CLASSIC_BACKGROUND_CLASSES:
            continue
        try:
            background = str(current.cget('background')).lower()
        except TclError:
            continue
        assert background not in light_backgrounds, (
            current,
            widget_class,
            background,
        )


def _apply_settled_theme(root: tk.Misc, theme_id: str) -> None:
    sv_ttk.set_theme(theme_id)
    root.update_idletasks()
    apply_theme_to_windows(theme_id)
    root.update_idletasks()
    root.update()


def cycle_light_dark(root: tk.Misc, scope: tk.Misc) -> None:
    _apply_settled_theme(root, 'light')
    _apply_settled_theme(root, 'dark')
    assert_dark_theme_applied(scope)


__all__ = ['assert_dark_theme_applied', 'cycle_light_dark']


if __name__ == '__main__':
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
