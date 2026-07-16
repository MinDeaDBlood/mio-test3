from __future__ import annotations

import tkinter as tk
from tkinter import X, Frame, Label, ttk

from src.ui.contracts import ByteCalculatorControllerPort
from src.ui.common.windowing import Toplevel
from src.ui.tabs.tools.byte_calculator import keys


class FileBytes(Toplevel):
    def __init__(
        self, *, language, units, controller: ByteCalculatorControllerPort
    ) -> None:
        super().__init__()
        self._language = language
        self.units = units
        self.controller = controller
        self.title(language.resolve_required_ui_text(keys.TITLE))
        self._is_calculating = False
        self.origin_size_var = tk.StringVar()
        self.result_size_var = tk.StringVar()
        self._build_ui()
        self.center_on_screen(force=True)

    def _build_ui(self) -> None:
        frame = Frame(self)
        frame.pack(pady=5, padx=5, fill=X, expand=True)
        self.origin_entry = ttk.Entry(frame, textvariable=self.origin_size_var)
        self.origin_entry.bind("<KeyRelease>", self.calc_forward)
        self.origin_entry.pack(side="left", padx=5, expand=True, fill=X)
        self.origin_unit = ttk.Combobox(
            frame, values=list(self.units), state="readonly", width=4
        )
        self.origin_unit.current(0)
        self.origin_unit.bind("<<ComboboxSelected>>", self._on_origin_unit_changed)
        self.origin_unit.pack(side="left", padx=5)
        Label(frame, text="=").pack(side="left", padx=5)
        self.result_entry = ttk.Entry(frame, textvariable=self.result_size_var)
        self.result_entry.bind("<KeyRelease>", self.calc_reverse)
        self.result_entry.pack(side="left", padx=5, expand=True, fill=X)
        self.target_unit = ttk.Combobox(
            frame, values=list(self.units), state="readonly", width=4
        )
        self.target_unit.current(0)
        self.target_unit.bind("<<ComboboxSelected>>", self._on_target_unit_changed)
        self.target_unit.pack(side="left", padx=5)
        ttk.Button(
            self,
            text=self._language.resolve_required_ui_text(keys.CLOSE_BUTTON),
            command=self.destroy,
        ).pack(fill=X, padx=5, pady=5)

    def _on_origin_unit_changed(self, _event=None) -> None:
        # The unit selector belongs to the left field. Keep the value on the
        # right as the source of truth and refresh the left field in its newly
        # selected unit.
        self.calc_reverse()

    def _on_target_unit_changed(self, _event=None) -> None:
        # The unit selector belongs to the right field. Keep the value on the
        # left as the source of truth and refresh the right field in its newly
        # selected unit.
        self.calc_forward()

    def _apply_conversion(
        self, source, destination, source_unit: str, target_unit: str
    ) -> None:
        value = self.controller.convert_value(source.get(), source_unit, target_unit)
        if destination.get() != value:
            destination.set(value)

    def calc_forward(self, _event=None) -> None:
        if self._is_calculating:
            return
        self._is_calculating = True
        try:
            self._apply_conversion(
                self.origin_size_var,
                self.result_size_var,
                self.origin_unit.get(),
                self.target_unit.get(),
            )
        finally:
            self._is_calculating = False

    def calc_reverse(self, _event=None) -> None:
        if self._is_calculating:
            return
        self._is_calculating = True
        try:
            self._apply_conversion(
                self.result_size_var,
                self.origin_size_var,
                self.target_unit.get(),
                self.origin_unit.get(),
            )
        finally:
            self._is_calculating = False


__all__ = ["FileBytes"]
