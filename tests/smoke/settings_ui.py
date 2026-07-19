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


import tkinter as tk
from tkinter import ttk

from src.app.localization_runtime import lang
from src.app.runtime.phases import require_registered_bootstrap_window_runtime
from src.ui.common.technical_choices import technical_label
from tests.support.runtime_smoke import prepare_root


def _walk(widget: tk.Misc):
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def main() -> None:
    root = prepare_root()
    try:
        root.update_idletasks()
        runtime = require_registered_bootstrap_window_runtime()
        widgets = list(_walk(root.tab3))
        assert widgets, 'The real settings composition produced no widgets.'

        combobox_values = [
            tuple(widget.cget('values'))
            for widget in widgets
            if isinstance(widget, ttk.Combobox)
        ]
        light_label = technical_label(lang, 'light')
        dark_label = technical_label(lang, 'dark')
        assert any(
            light_label in values and dark_label in values
            for values in combobox_values
        )
        assert any(
            runtime.language.get() in values and len(values) >= 2
            for values in combobox_values
        )

        buttons = [widget for widget in widgets if isinstance(widget, ttk.Button)]
        toggles = [
            widget
            for widget in widgets
            if isinstance(widget, (ttk.Checkbutton, ttk.Radiobutton))
        ]
        scales = [widget for widget in widgets if isinstance(widget, ttk.Scale)]
        assert buttons and toggles and scales
        assert all(str(widget.cget('text')).strip() for widget in buttons)
        assert runtime.theme.get() in {'light', 'dark'}
        assert runtime.language.get() in {'English', 'Russian'}
    finally:
        root.destroy()

    print('SETTINGS_UI_SMOKE_OK')


if __name__ == '__main__':
    main()
