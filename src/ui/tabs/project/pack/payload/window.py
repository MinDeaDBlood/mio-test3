from __future__ import annotations

from tkinter import BOTH, ttk

from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project.pack.payload import keys


class PayloadPackUnavailableWindow(Toplevel):
    def __init__(self, *, texts: LocalizationCatalog, reason: str) -> None:
        super().__init__()
        self.title(texts.resolve_required_ui_text(keys.TITLE))
        frame = ttk.Frame(self)
        frame.pack(fill=BOTH, expand=True, padx=16, pady=16)
        ttk.Label(
            frame,
            text=texts.resolve_required_ui_text(keys.UNAVAILABLE),
            font=(None, 12, "bold"),
        ).pack(anchor="w")
        ttk.Label(frame, text=reason, wraplength=420, justify="left").pack(
            anchor="w", pady=(8, 12)
        )
        ttk.Button(
            frame,
            text=texts.resolve_required_ui_text(keys.OK_BUTTON),
            command=self.destroy,
        ).pack(anchor="e")


__all__ = ["PayloadPackUnavailableWindow"]
