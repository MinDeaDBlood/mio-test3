from __future__ import annotations

import logging
import sys
import tkinter as tk
from collections.abc import Callable
from functools import lru_cache
from io import BytesIO
from tkinter import BOTH, BOTTOM, X, Frame, Label, Text, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.contracts import DebuggerControllerPort
from src.ui.common.windowing import Toplevel
from src.ui.log_interface import debugger_keys as keys


@lru_cache(maxsize=1)
def _resolve_pil_image_helpers():
    from PIL.Image import open as open_img
    from PIL.ImageTk import PhotoImage

    return open_img, PhotoImage


@lru_cache(maxsize=1)
def _load_miside_banner_bytes():
    from src.ui.assets.miside_banner import banner_image

    return banner_image


class Debugger(Toplevel):
    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        controller: DebuggerControllerPort,
        generate_bug_report: Callable[[], object],
        open_url: Callable[[str], object],
        show_banner: bool,
    ) -> None:
        super().__init__()
        self._texts = texts
        self._controller = controller
        self._generate_bug_report = generate_bug_report
        self._open_url = open_url
        self._show_banner = show_banner
        self.title(texts.resolve_required_ui_text(keys.TITLE))
        self._build_ui()
        self.center_on_screen(force=True)

    def _build_ui(self) -> None:
        if self._show_banner:
            open_img, PhotoImage = _resolve_pil_image_helpers()
            image = open_img(BytesIO(_load_miside_banner_bytes())).resize((640, 206))
            self._banner_image = PhotoImage(image)
            Label(self, image=self._banner_image).grid(row=0, column=0, columnspan=3)

        actions = (
            (self._texts.resolve_required_ui_text(keys.GLOBALS), self.loaded_module),
            (self._texts.resolve_required_ui_text(keys.SETTINGS), self.settings),
            (self._texts.resolve_required_ui_text(keys.INFO), self.show_info),
            (self._texts.resolve_required_ui_text(keys.CRASH), self.crash),
            (
                self._texts.resolve_required_ui_text(keys.HACKER_PANEL),
                lambda: self._open_url(
                    "https://vdse.bdstatic.com/192d9a98d782d9c74c96f09db9378d93.mp4"
                ),
            ),
            (
                self._texts.resolve_required_ui_text(keys.GENERATE_BUG_REPORT),
                self._generate_bug_report,
            ),
            (
                "米塔 MiSide",
                lambda: self._open_url("https://store.steampowered.com/app/2527500/"),
            ),
            ("米塔 MiSide(Demo)", lambda: self._open_url("steam://install/2527520")),
            ("No More Room in Hell", lambda: self._open_url("steam://install/224260")),
        )
        row, column = 1, 0
        for text, command in actions:
            ttk.Button(
                self, text=text, command=command, width=20, style="Toggle.TButton"
            ).grid(row=row, column=column, padx=5, pady=5)
            column = (column + 1) % 3
            if not column:
                row += 1

    @staticmethod
    def crash() -> None:
        sys.stderr.write("Crashed!")
        sys.stderr.flush()

    def show_info(self) -> None:
        window = Toplevel()
        window.title(self._texts.resolve_required_ui_text(keys.INFO))
        ttk.Label(
            window,
            text=self._texts.resolve_required_ui_text(keys.INFO_BRAND_LABEL),
            font=(None, 15),
            foreground="orange",
            anchor="center",
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ns")
        text_widget = Text(window, foreground="gray")
        text_widget.insert(1.0, self._controller.build_info_text())
        text_widget.grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        window.center_on_screen(force=True)

    def _show_key_value_editor(
        self, *, title: str, keys: tuple[str, ...], read_value, write_value
    ) -> None:
        def read_selected() -> None:
            value_entry.delete(0, tk.END)
            value_entry.insert(0, read_value(key_box.get()))

        def save() -> None:
            if not value_entry.get():
                read_selected()
                return
            try:
                value = write_value(key_box.get(), value_entry.get())
            except Exception:
                logging.exception("Debugger editor save failed")
                return
            value_entry.delete(0, tk.END)
            value_entry.insert(0, value)

        window = Toplevel()
        window.title(title)
        frame = Frame(window)
        frame.pack(pady=5, padx=5, fill=X, expand=True)
        key_box = ttk.Combobox(frame, values=keys, state="readonly")
        if keys:
            key_box.current(0)
        key_box.bind("<<ComboboxSelected>>", lambda *_args: read_selected())
        key_box.pack(side="left", padx=5)
        Label(frame, text=":").pack(side="left", padx=5)
        value_entry = ttk.Entry(frame, state="normal")
        value_entry.bind("<KeyRelease>", lambda _event: save())
        value_entry.pack(padx=5, fill=BOTH)
        if keys:
            read_selected()
        ttk.Button(
            window,
            text=self._texts.resolve_required_ui_text(keys.INFO_DIALOG_OK_BUTTON),
            command=window.destroy,
        ).pack(fill=X, side=BOTTOM)
        window.center_on_screen(force=True)
        window.wait_window()

    def settings(self) -> None:
        self._show_key_value_editor(
            title=self._texts.resolve_required_ui_text(keys.SETTINGS),
            keys=self._controller.setting_keys(),
            read_value=self._controller.read_setting,
            write_value=self._controller.write_setting,
        )

    def loaded_module(self) -> None:
        self._show_key_value_editor(
            title=self._texts.resolve_required_ui_text(keys.GLOBALS),
            keys=self._controller.global_keys(),
            read_value=self._controller.read_global,
            write_value=self._controller.write_global,
        )


__all__ = ["Debugger"]
