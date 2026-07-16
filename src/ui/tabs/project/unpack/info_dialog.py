from __future__ import annotations

import tkinter as tk
from tkinter import BOTH, CENTER, RIGHT, X, Y, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.common.windowing import Toplevel
from src.ui.tabs.project.unpack import info_dialog_keys as keys


def show_unpack_image_info_dialog(
    *, texts: LocalizationCatalog, info_rows, title: str | None = None
):
    dialog = Toplevel()
    dialog.center_on_screen(force=True)
    dialog.title(title or texts.resolve_required_ui_text(keys.DEFAULT_TITLE))
    scroll = ttk.Scrollbar(dialog, orient="vertical")
    columns = [
        texts.resolve_required_ui_text(keys.NAME_COLUMN),
        texts.resolve_required_ui_text(keys.VALUE_COLUMN),
    ]
    table = ttk.Treeview(
        master=dialog,
        height=10,
        columns=columns,
        show="headings",
        yscrollcommand=scroll.set,
    )
    for column in columns:
        table.heading(column=column, text=column, anchor=CENTER)
        table.column(column=column, anchor=CENTER)
    scroll.config(command=table.yview)
    scroll.pack(side=RIGHT, fill=Y)
    table.pack(fill=BOTH, expand=True)
    for data in info_rows:
        table.insert("", tk.END, values=data)
    ttk.Button(
        dialog,
        text=texts.resolve_required_ui_text(keys.OK_BUTTON),
        command=dialog.destroy,
    ).pack(padx=5, pady=5, fill=X)
    return dialog


__all__ = ["show_unpack_image_info_dialog"]
