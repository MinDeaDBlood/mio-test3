from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterable
from tkinter import X, ttk

from src.ui.common import windowing_keys as keys
from src.ui.localization import LocalizationCatalog


class CustomControls:
    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        choose_file: Callable[[], str],
        choose_directory: Callable[[], str],
    ) -> None:
        self._texts = texts
        self._choose_file = choose_file
        self._choose_directory = choose_directory

    def filechose(
        self,
        master: tk.Misc,
        textvariable: tk.Variable,
        text: str,
        *,
        is_folder: bool = False,
        browse_text: str | None = None,
    ) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.pack(fill=X)
        ttk.Label(
            frame,
            text=text,
            width=15,
            font=("TkDefaultFont", 12),
        ).pack(side="left", padx=10, pady=10)
        ttk.Entry(frame, textvariable=textvariable).pack(
            side="left",
            padx=5,
            pady=5,
        )
        chooser = self._choose_directory if is_folder else self._choose_file
        ttk.Button(
            frame,
            text=browse_text
            or self._texts.resolve_required_ui_text(keys.COMMON_WINDOWING_BROWSE),
            command=lambda: textvariable.set(chooser()),
        ).pack(side="left", padx=10, pady=10)
        return frame

    @staticmethod
    def combobox(
        master: tk.Misc,
        textvariable: tk.Variable,
        values: Iterable[str],
        text: str,
    ) -> ttk.Combobox:
        frame = ttk.Frame(master)
        frame.pack(fill=X)
        ttk.Label(
            frame,
            text=text,
            width=15,
            font=("TkDefaultFont", 12),
        ).pack(side="left", padx=10, pady=10)
        combo = ttk.Combobox(
            frame,
            textvariable=textvariable,
            values=tuple(values),
            state="readonly",
        )
        combo.pack(side="left", padx=5, pady=5)
        combo_values = tuple(combo["values"])
        if combo_values and not textvariable.get():
            textvariable.set(combo_values[0])
        return combo


__all__ = ["CustomControls"]
