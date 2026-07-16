from __future__ import annotations

import tkinter as tk
from tkinter import BOTH, LEFT, TOP, X, Text, ttk
from typing import Callable

from src.ui.common.windowing import Toplevel
from src.ui.update import keys


class UpdaterWindow(Toplevel):
    """Tk presentation for the update workflow."""

    def __init__(
        self,
        *,
        version: str,
        texts: object,
        source_mode: bool,
        source_update_available: bool,
        on_update_requested: Callable[[], object],
        on_close_requested: Callable[[], object],
    ) -> None:
        super().__init__()
        self.texts = texts
        self._on_update_requested = on_update_requested
        self._on_close_requested = on_close_requested
        self.title(texts.resolve_required_ui_text(keys.WINDOW_TITLE))
        self.protocol("WM_DELETE_WINDOW", self._on_close_requested)
        self._build_view(
            version=version,
            source_mode=source_mode,
            source_update_available=source_update_available,
        )

    def _build_view(
        self, *, version: str, source_mode: bool, source_update_available: bool
    ) -> None:
        header = ttk.Frame(self)
        ttk.Label(
            header,
            text=self.texts.resolve_required_ui_text(keys.BRAND_LABEL),
            font=(None, 20),
        ).pack(side=LEFT, padx=5, pady=2)
        ttk.Label(header, text=version, foreground="gray").pack(
            side=LEFT, padx=2, pady=2
        )
        header.pack(padx=5, pady=5, side=TOP)

        content = ttk.LabelFrame(self, text=self.texts.resolve_required_ui_text(keys.UPDATE_WINDOW_UPDATE_INFORMATION))
        self.notice = ttk.Label(
            content, text=self.texts.resolve_required_ui_text(keys.UPDATE_WINDOW_CHECK_UPDATES_HINT)
        )
        self.notice.pack(padx=5, pady=5)
        if source_mode and not source_update_available:
            ttk.Label(
                self,
                text=self.texts.resolve_required_ui_text(
                    keys.GIT_NOT_INSTALLED_MESSAGE
                ),
                foreground="orange",
                font=(None, 12),
            ).pack(padx=5, pady=5)
            self.change_log = None
            self.progressbar = None
            self.update_button = None
            self.center_on_screen(force=True)
            return

        self.change_log = Text(content, width=50, height=15)
        self.change_log.pack(padx=5, pady=5)
        content.pack(fill=BOTH, padx=5, pady=5)

        self.progressbar = ttk.Progressbar(
            self,
            length=200,
            mode="determinate",
            orient="horizontal",
            maximum=100,
        )
        self.progressbar.pack(padx=5, pady=10)
        buttons = ttk.Frame(self)
        self.update_button = ttk.Button(
            buttons,
            text=self.texts.resolve_required_ui_text(keys.CHECK_UPDATES_BUTTON),
            style="Accent.TButton",
            command=self._on_update_requested,
        )
        ttk.Button(
            buttons,
            text=self.texts.resolve_required_ui_text(keys.CANCEL_BUTTON),
            command=self._on_close_requested,
        ).pack(fill=X, expand=True, side=LEFT, pady=10, padx=10)
        self.update_button.pack(fill=X, expand=True, side=LEFT, pady=10, padx=10)
        buttons.pack(padx=5, pady=5, fill=X)
        self.resizable(width=False, height=False)
        self.center_on_screen(force=True)

    def is_ready(self) -> bool:
        return self.update_button is not None

    def clear_change_log(self) -> None:
        if self.change_log is not None:
            self.change_log.delete(1.0, tk.END)

    def append_change_log(self, text: str) -> None:
        if self.change_log is not None:
            self.change_log.insert("insert", text)

    def set_notice(self, text: str, *, color: str = "") -> None:
        self.notice.configure(text=text, foreground=color)

    def set_action_button(self, *, text: str, enabled: bool = True) -> None:
        if self.update_button is not None:
            self.update_button.configure(
                text=text, state="normal" if enabled else "disabled"
            )

    def show_busy(self, *, notice_text: str, button_text: str) -> None:
        self.set_notice(notice_text, color="orange")
        self.set_action_button(text=button_text, enabled=False)
        if self.progressbar is not None:
            self.progressbar.configure(mode="indeterminate")
            self.progressbar.start()

    def reset_progress(self) -> None:
        if self.progressbar is not None:
            self.progressbar.stop()
            self.progressbar.configure(mode="determinate")
            self.progressbar["value"] = 0

    def set_progress(self, percentage: int) -> None:
        if self.progressbar is None:
            return
        self.progressbar.configure(mode="determinate")
        self.progressbar.stop()
        self.progressbar["value"] = percentage
        self.progressbar.update()


__all__ = ["UpdaterWindow"]
