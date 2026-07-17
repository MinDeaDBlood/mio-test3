from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import TclError, ttk
from typing import Any

from src.ui.common.themes.identifiers import DARK_THEME, LIGHT_THEME, require_theme_id


@dataclass(frozen=True)
class ThemePalette:
    window_background: str
    surface_background: str
    input_background: str
    foreground: str
    muted_foreground: str
    active_background: str
    selection_background: str
    selection_foreground: str
    border: str
    disabled_foreground: str


_DARK_PALETTE = ThemePalette(
    window_background='#1c1c1c',
    surface_background='#1c1c1c',
    input_background='#2b2b2b',
    foreground='#fafafa',
    muted_foreground='#a8a8a8',
    active_background='#333333',
    selection_background='#2f60d8',
    selection_foreground='#ffffff',
    border='#454545',
    disabled_foreground='#7a7a7a',
)

_LIGHT_PALETTE = ThemePalette(
    window_background='#fafafa',
    surface_background='#fafafa',
    input_background='#ffffff',
    foreground='#1c1c1c',
    muted_foreground='#666666',
    active_background='#e8e8e8',
    selection_background='#2f60d8',
    selection_foreground='#ffffff',
    border='#c9c9c9',
    disabled_foreground='#8a8a8a',
)

_PALETTES = {
    DARK_THEME: _DARK_PALETTE,
    LIGHT_THEME: _LIGHT_PALETTE,
}

_LEGACY_THEME_COLORS = {
    '#101010',
    '#f0f0f0',
}

_SYSTEM_THEME_COLORS = {
    '',
    'black',
    'white',
    '#000000',
    '#ffffff',
    'systembuttonface',
    'systembuttontext',
    'systemwindow',
    'systemwindowtext',
    'systemhighlight',
    'systemhighlighttext',
    'systemgraytext',
}

_MANAGED_THEME_COLORS = frozenset(
    value.lower()
    for palette in _PALETTES.values()
    for value in (
        palette.window_background,
        palette.surface_background,
        palette.input_background,
        palette.foreground,
        palette.active_background,
        palette.selection_background,
        palette.selection_foreground,
        palette.border,
        palette.disabled_foreground,
    )
) | frozenset(value.lower() for value in _LEGACY_THEME_COLORS | _SYSTEM_THEME_COLORS)


_CLASSIC_WIDGET_OPTIONS: dict[str, dict[str, str]] = {
    'Frame': {
        'background': 'surface_background',
        'highlightbackground': 'border',
    },
    'Labelframe': {
        'background': 'surface_background',
        'foreground': 'foreground',
        'highlightbackground': 'border',
    },
    'Label': {
        'background': 'surface_background',
        'foreground': 'foreground',
        'highlightbackground': 'border',
    },
    'Button': {
        'background': 'input_background',
        'foreground': 'foreground',
        'activebackground': 'active_background',
        'activeforeground': 'foreground',
        'disabledforeground': 'disabled_foreground',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
    'Checkbutton': {
        'background': 'surface_background',
        'foreground': 'foreground',
        'activebackground': 'active_background',
        'activeforeground': 'foreground',
        'disabledforeground': 'disabled_foreground',
        'selectcolor': 'input_background',
        'highlightbackground': 'border',
    },
    'Radiobutton': {
        'background': 'surface_background',
        'foreground': 'foreground',
        'activebackground': 'active_background',
        'activeforeground': 'foreground',
        'disabledforeground': 'disabled_foreground',
        'selectcolor': 'input_background',
        'highlightbackground': 'border',
    },
    'Text': {
        'background': 'input_background',
        'foreground': 'foreground',
        'insertbackground': 'foreground',
        'selectbackground': 'selection_background',
        'selectforeground': 'selection_foreground',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
    'Listbox': {
        'background': 'input_background',
        'foreground': 'foreground',
        'selectbackground': 'selection_background',
        'selectforeground': 'selection_foreground',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
    'Entry': {
        'background': 'input_background',
        'foreground': 'foreground',
        'insertbackground': 'foreground',
        'selectbackground': 'selection_background',
        'selectforeground': 'selection_foreground',
        'disabledforeground': 'disabled_foreground',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
    'Spinbox': {
        'background': 'input_background',
        'foreground': 'foreground',
        'insertbackground': 'foreground',
        'selectbackground': 'selection_background',
        'selectforeground': 'selection_foreground',
        'disabledforeground': 'disabled_foreground',
        'buttonbackground': 'input_background',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
    'Menu': {
        'background': 'input_background',
        'foreground': 'foreground',
        'activebackground': 'selection_background',
        'activeforeground': 'selection_foreground',
        'disabledforeground': 'disabled_foreground',
        'selectcolor': 'foreground',
    },
    'Canvas': {
        'background': 'surface_background',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
    'Scale': {
        'background': 'surface_background',
        'foreground': 'foreground',
        'activebackground': 'active_background',
        'troughcolor': 'input_background',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
    'Scrollbar': {
        'background': 'input_background',
        'activebackground': 'active_background',
        'troughcolor': 'surface_background',
        'highlightbackground': 'border',
        'highlightcolor': 'selection_background',
    },
}

_OPTION_DATABASE_PATTERNS: dict[str, str] = {
    '*Text.background': 'input_background',
    '*Text.foreground': 'foreground',
    '*Text.insertBackground': 'foreground',
    '*Text.selectBackground': 'selection_background',
    '*Text.selectForeground': 'selection_foreground',
    '*Text.highlightBackground': 'border',
    '*Text.highlightColor': 'selection_background',
    '*Listbox.background': 'input_background',
    '*Listbox.foreground': 'foreground',
    '*Listbox.selectBackground': 'selection_background',
    '*Listbox.selectForeground': 'selection_foreground',
    '*Listbox.highlightBackground': 'border',
    '*Listbox.highlightColor': 'selection_background',
    '*Entry.background': 'input_background',
    '*Entry.foreground': 'foreground',
    '*Entry.insertBackground': 'foreground',
    '*Entry.selectBackground': 'selection_background',
    '*Entry.selectForeground': 'selection_foreground',
    '*Spinbox.background': 'input_background',
    '*Spinbox.foreground': 'foreground',
    '*Spinbox.insertBackground': 'foreground',
    '*Spinbox.selectBackground': 'selection_background',
    '*Spinbox.selectForeground': 'selection_foreground',
    '*Menu.background': 'input_background',
    '*Menu.foreground': 'foreground',
    '*Menu.activeBackground': 'selection_background',
    '*Menu.activeForeground': 'selection_foreground',
    '*Canvas.background': 'surface_background',
    '*Frame.background': 'surface_background',
    '*Labelframe.background': 'surface_background',
    '*Labelframe.foreground': 'foreground',
    '*Label.background': 'surface_background',
    '*Label.foreground': 'foreground',
    '*Button.background': 'input_background',
    '*Button.foreground': 'foreground',
    '*Button.activeBackground': 'active_background',
    '*Button.activeForeground': 'foreground',
    '*Checkbutton.background': 'surface_background',
    '*Checkbutton.foreground': 'foreground',
    '*Checkbutton.selectColor': 'input_background',
    '*Radiobutton.background': 'surface_background',
    '*Radiobutton.foreground': 'foreground',
    '*Radiobutton.selectColor': 'input_background',
    '*TCombobox*Listbox.background': 'input_background',
    '*TCombobox*Listbox.foreground': 'foreground',
    '*TCombobox*Listbox.selectBackground': 'selection_background',
    '*TCombobox*Listbox.selectForeground': 'selection_foreground',
}


def get_theme_palette(theme_id: str) -> ThemePalette:
    return _PALETTES[require_theme_id(theme_id)]


def _root_widget(widget: tk.Misc) -> tk.Misc:
    try:
        return widget._root()
    except (AttributeError, TclError):
        return widget


def install_native_theme_defaults(widget: tk.Misc, theme_id: str) -> ThemePalette:
    palette = get_theme_palette(theme_id)
    root = _root_widget(widget)
    for pattern, role in _OPTION_DATABASE_PATTERNS.items():
        try:
            root.option_add(pattern, getattr(palette, role), 'interactive')
        except (AttributeError, TclError):
            break
    return palette


def _is_managed_color(value: object) -> bool:
    return str(value).strip().lower() in _MANAGED_THEME_COLORS


def _apply_managed_option(widget: tk.Misc, option: str, value: str) -> None:
    try:
        current = widget.cget(option)
    except (AttributeError, TclError):
        return
    if not _is_managed_color(current):
        return
    try:
        widget.configure(**{option: value})
    except (AttributeError, TclError):
        return


def _apply_classic_widget(widget: tk.Misc, palette: ThemePalette) -> None:
    try:
        widget_class = str(widget.winfo_class())
    except (AttributeError, TclError):
        return
    option_roles = _CLASSIC_WIDGET_OPTIONS.get(widget_class)
    if option_roles is None:
        return
    for option, role in option_roles.items():
        _apply_managed_option(widget, option, getattr(palette, role))


def _apply_combobox_popdown(widget: ttk.Combobox, palette: ThemePalette) -> None:
    try:
        popdown = str(widget.tk.call('ttk::combobox::PopdownWindow', widget._w))
        listbox_path = f'{popdown}.f.l'
        widget.tk.call(
            listbox_path,
            'configure',
            '-background',
            palette.input_background,
            '-foreground',
            palette.foreground,
            '-selectbackground',
            palette.selection_background,
            '-selectforeground',
            palette.selection_foreground,
            '-highlightbackground',
            palette.border,
            '-highlightcolor',
            palette.selection_background,
        )
    except (AttributeError, TclError):
        return


def _walk_widget_tree(widget: tk.Misc) -> tuple[tk.Misc, ...]:
    discovered: list[tk.Misc] = []
    stack: list[tk.Misc] = [widget]
    while stack:
        current = stack.pop()
        discovered.append(current)
        try:
            children = tuple(current.winfo_children())
        except (AttributeError, TclError):
            continue
        stack.extend(reversed(children))
    return tuple(discovered)


def apply_native_theme(widget: Any, theme_id: str) -> ThemePalette:
    typed_widget = widget
    palette = install_native_theme_defaults(typed_widget, theme_id)
    for current in _walk_widget_tree(typed_widget):
        _apply_classic_widget(current, palette)
        if isinstance(current, ttk.Combobox):
            _apply_combobox_popdown(current, palette)
    return palette


__all__ = [
    'ThemePalette',
    'apply_native_theme',
    'get_theme_palette',
    'install_native_theme_defaults',
]
