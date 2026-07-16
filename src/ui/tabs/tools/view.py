from __future__ import annotations

from tkinter import BOTH, HORIZONTAL, X, ttk

from src.ui.tabs.tools import keys
from src.ui.tabs.tools.toolbox import ToolBox


def build_tools_tab(window, *, openers, texts, ensure_texts_loaded) -> None:
    ttk.Label(window.tab6, text=texts.resolve_required_ui_text(keys.TITLE), font=(None, 20)).pack(
        padx=10,
        pady=10,
        fill=BOTH,
    )
    ttk.Separator(window.tab6, orient=HORIZONTAL).pack(padx=10, pady=10, fill=X)
    tool_box = ToolBox(window.tab6, openers=openers, texts=texts, ensure_texts_loaded=ensure_texts_loaded)
    tool_box.gui()
    tool_box.pack(fill=BOTH, expand=True)


__all__ = ['build_tools_tab']
