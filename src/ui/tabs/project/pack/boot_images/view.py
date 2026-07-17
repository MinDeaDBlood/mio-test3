from __future__ import annotations

from collections.abc import Callable
from tkinter import BOTH, X
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.common.windowing import Toplevel
from src.ui.common.technical_choices import build_choice_set
from src.ui.tabs.project.pack.boot_images import keys


class BootImagesPack(Toplevel):
    def __init__(
        self, *, texts: LocalizationCatalog, on_run: Callable[[str], object], master=None
    ) -> None:
        super().__init__(master=master)
        self._texts = texts
        self.title(self._texts.resolve_required_ui_text(keys.WINDOW_TITLE))
        self._mode_choices = build_choice_set(
            self._texts, ("boot", "recovery", "vendor_boot")
        )
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
        self.mode_box = ttk.Combobox(
            wrapper,
            state="readonly",
            values=self._mode_choices.labels,
        )
        self.mode_box.current(self._mode_choices.index_for("boot"))
        self.mode_box.pack(fill=X, padx=5, pady=5)
        ttk.Button(
            wrapper,
            text=self._texts.resolve_required_ui_text(keys.PACK_BUTTON),
            style="Accent.TButton",
            command=self._submit,
        ).pack(
            fill=X,
            padx=5,
            pady=5,
        )

    def _submit(self) -> None:
        mode = self._mode_choices.value_at(self.mode_box.current())
        self.destroy()
        self._on_run(mode)


__all__ = ["BootImagesPack"]
