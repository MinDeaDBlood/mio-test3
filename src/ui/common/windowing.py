from __future__ import annotations

from src.ui.common import windowing_keys as keys
import tkinter as tk
from collections.abc import Callable, Iterable
from typing import Any
from tkinter import TclError, Toplevel as TkToplevel, X, ttk

from src.ui.common.window_appearance import register_window
from src.ui.localization import LocalizationCatalog


class Toplevel(TkToplevel):
    """Project Toplevel with shared title bar theming and centering."""

    def __init__(
        self,
        master: tk.Misc | None = None,
        *,
        center_on_open: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(master=master, **kwargs)
        register_window(self)
        self._centered_once = False
        if center_on_open:
            self.center_after_layout()

    def center_after_layout(self, *, force: bool = False) -> None:
        self.after_idle(lambda: self.center_on_screen(force=force))

    def center_on_screen(self, *, force: bool = False) -> None:
        if self._centered_once and not force:
            return
        try:
            from src.ui.common.geometry import move_center

            move_center(self)
        except (TclError, RuntimeError):
            return
        self._centered_once = True


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
            text=browse_text or self._texts.resolve_required_ui_text(keys.COMMON_WINDOWING_BROWSE),
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


__all__ = ["Toplevel", "CustomControls"]
