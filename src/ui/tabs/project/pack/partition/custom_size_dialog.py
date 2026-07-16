from __future__ import annotations

import tkinter as tk
from collections.abc import MutableMapping, Sequence
from tkinter import BOTTOM, X, Frame, Label
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.common.windowing import Toplevel
from src.ui.tabs.project.pack.partition import keys


def edit_custom_ext4_sizes(
    *,
    texts: LocalizationCatalog,
    chosen_parts: Sequence[str],
    custom_size: MutableMapping[str, int | str],
    initial_sizes: MutableMapping[str, int | str],
) -> None:
    """Open the legacy custom-size editor while keeping size resolution out of the window.

    The dialog intentionally preserves the old layout and mutates ``custom_size``
    in-place, matching the existing PackPartition behavior.
    """

    def save() -> None:
        value = entry.get()
        if value.isdigit():
            custom_size[partition_selector.get()] = value
        elif not value:
            return
        else:
            read_value()

    def read_value() -> None:
        entry.delete(0, tk.END)
        entry.insert(0, str(custom_size.get(partition_selector.get(), 0)))

    custom_size.clear()
    custom_size.update(initial_sizes)
    dialog = Toplevel()
    dialog.title(texts.resolve_required_ui_text(keys.PROJECT_PACK_PARTITION_CUSTOM_SIZE_DIALOG_MODIFY_SIZE))
    frame = Frame(dialog)
    frame.pack(pady=5, padx=5, fill=X)
    partition_selector = ttk.Combobox(
        frame, values=list(custom_size.keys()), state="readonly"
    )
    if custom_size:
        partition_selector.current(0)
    partition_selector.bind("<<ComboboxSelected>>", lambda *_args: read_value())
    partition_selector.pack(side="left", padx=5)
    Label(frame, text=":").pack(side="left", padx=5)
    entry = ttk.Entry(frame, state="normal")
    entry.bind("<KeyRelease>", lambda _event: save())
    entry.pack(side="left", padx=5)
    read_value()
    ttk.Button(
        dialog,
        text=texts.resolve_required_ui_text(keys.CUSTOM_SIZE_OK_BUTTON),
        command=dialog.destroy,
    ).pack(fill=X, side=BOTTOM)
    dialog.center_on_screen(force=True)
    dialog.wait_window()


__all__ = ["edit_custom_ext4_sizes"]
