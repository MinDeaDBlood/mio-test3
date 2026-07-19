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


import sys
from tkinter import ttk

from tests.support.runtime_smoke import prepare_root
from src.app.composition.debugger import open_debugger_window
from src.app.composition.plugin_manager import create_plugin_manager_view


def main() -> None:
    root = prepare_root()
    try:
        language_credits = [
            widget
            for widget in root.tab4.winfo_children()
            if isinstance(widget, ttk.Label)
            and str(widget.cget('foreground')) == 'orange'
        ]
        assert len(language_credits) == 1, 'About language credit was not rendered.'
        assert not str(language_credits[0].cget('background')), (
            'About language credit must inherit the tab background.'
        )

        debugger = open_debugger_window()
        debugger.withdraw()
        debugger.update_idletasks()
        debugger.destroy()

        manager = create_plugin_manager_view(master=root.tab7, host_window=root)
        manager.gui()
        manager.update_idletasks()
        assert manager.winfo_children(), 'Plugin manager view was not rendered.'
        manager.destroy()

        assert root.tab6.winfo_children(), 'Toolbox tab was not composed.'

        legacy_modules = {
            'src.app.runtime_session',
            'src.app.runtime_state',
            'src.app.tk_runtime',
            'src.ui.tabs.plugins._mpk_windows',
            'src.ui.tabs.project.common',
        }
        assert not (legacy_modules & set(sys.modules)), 'Legacy runtime or UI facades were imported.'
    finally:
        root.destroy()

    print('RUNTIME_SMOKE_OK')


if __name__ == '__main__':
    main()
