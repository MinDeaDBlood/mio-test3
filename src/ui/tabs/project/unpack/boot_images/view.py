from __future__ import annotations

from collections.abc import Callable
from tkinter import BOTH, X, StringVar
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.common.windowing import Toplevel
from src.ui.tabs.project.unpack.boot_images import keys


class BootImagesUnpack(Toplevel):
    def __init__(
        self, *, texts: LocalizationCatalog, on_run: Callable[[str], object], master=None
    ) -> None:
        super().__init__(master=master)
        self._texts = texts
        self.title(self._texts.resolve_required_ui_text(keys.WINDOW_TITLE))
        self.mode = StringVar(master=self, value="boot")
        self._on_run = on_run
        self._build()
        self.center_on_screen(force=True)

    def set_run_action(self, on_run: Callable[[str], object]) -> None:
        self._on_run = on_run

    def _build(self) -> None:
        wrapper = ttk.Frame(self)
        wrapper.pack(padx=10, pady=10, fill=BOTH, expand=True)
        ttk.Label(
            wrapper, text=self._texts.resolve_required_ui_text(keys.IMAGE_TYPE_LABEL)
        ).pack(fill=X, padx=5, pady=5)
        ttk.Combobox(
            wrapper,
            state="readonly",
            textvariable=self.mode,
            values=("boot", "recovery", "vendor_boot"),
        ).pack(fill=X, padx=5, pady=5)
        ttk.Button(
            wrapper,
            text=self._texts.resolve_required_ui_text(keys.UNPACK_BUTTON),
            style="Accent.TButton",
            command=self._submit,
        ).pack(
            fill=X,
            padx=5,
            pady=5,
        )

    def _submit(self) -> None:
        mode = self.mode.get()
        self.destroy()
        self._on_run(mode)


__all__ = ["BootImagesUnpack"]
