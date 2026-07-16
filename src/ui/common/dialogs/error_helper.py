from __future__ import annotations

from tkinter import BOTH, ttk

from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.common.dialogs import error_helper_keys as keys


def show_error_helper(
    *,
    texts: LocalizationCatalog,
    source_text: str,
    detail: str,
    solution: str,
    confidence: int,
    ok_text: str,
) -> None:
    window = Toplevel()
    window.resizable(False, False)
    window.title(texts.resolve_required_ui_text(keys.TITLE))

    detail_frame = ttk.LabelFrame(window, text=texts.resolve_required_ui_text(keys.DETAIL))
    ttk.Label(detail_frame, text=source_text, font=(None, 12), foreground='orange', wraplength=400).pack(
        padx=10,
        pady=5,
    )
    ttk.Label(detail_frame, text=detail, font=(None, 15), foreground='grey', wraplength=400).pack(
        padx=10,
        pady=10,
    )
    confidence_text = texts.resolve_required_ui_text(keys.MATCH_CONFIDENCE).format(value=confidence)
    ttk.Label(detail_frame, text=confidence_text, font=(None, 10), foreground='grey', wraplength=400).pack(
        padx=10,
        pady=(0, 10),
    )
    detail_frame.pack(padx=10, pady=10)

    solution_frame = ttk.LabelFrame(window, text=texts.resolve_required_ui_text(keys.SOLUTION))
    ttk.Label(solution_frame, text=solution, font=(None, 15), foreground='green', wraplength=400).pack(
        padx=10,
        pady=10,
    )
    solution_frame.pack(padx=10, pady=10)

    ttk.Button(window, text=ok_text, command=window.destroy, style='Accent.TButton').pack(
        padx=10,
        pady=10,
        fill=BOTH,
    )
    window.center_on_screen(force=True)


__all__ = ['show_error_helper']
