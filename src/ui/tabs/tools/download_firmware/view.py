from __future__ import annotations

from collections.abc import Callable
from tkinter import BooleanVar, StringVar, ttk

from src.ui.tabs.tools.download_firmware import keys


class FirmwareDownloadView:
    """Presentation object for the firmware download surface."""

    def __init__(self, *, host_window: object, texts: object) -> None:
        self.host_window = host_window
        self.texts = texts
        self.auto_import = BooleanVar(value=False)
        self.status = StringVar(value="")
        self.frame = None
        self.progressbar = None

    def _text(self, key: str) -> str:
        return self.texts.resolve_required_ui_text(key)

    def ask_url(self, input_func: Callable[..., str | None]) -> str | None:
        return input_func(
            texts=self.texts,
            title=self._text(keys.URL_DIALOG_TITLE),
            master=self.host_window,
        )

    def empty_url_message(self) -> str:
        return self._text(keys.EMPTY_URL_MESSAGE)

    def show_validation_error(self, message: str) -> None:
        self.host_window.message_pop(message, "red")

    def open(self, url: str, *, display_name: str) -> None:
        self.host_window.message_pop(self._text(keys.TASK_ADDED_MESSAGE), "green")
        self.frame = self.host_window.get_frame(self._text(keys.DOWNLOAD_GROUP_TITLE))
        self.progressbar = ttk.Progressbar(self.frame, length=200, mode="determinate")
        self.progressbar.pack(padx=10, pady=10)
        ttk.Label(self.frame, text=display_name, justify="left").pack(padx=10, pady=5)
        ttk.Label(self.frame, text=url, wraplength=200, justify="left").pack(
            padx=10, pady=5
        )
        ttk.Label(self.frame, textvariable=self.status).pack(padx=10, pady=10)
        ttk.Checkbutton(
            self.frame,
            text=self._text(keys.AUTO_IMPORT_CHECKBOX),
            variable=self.auto_import,
            onvalue=True,
            offvalue=False,
        ).pack(padx=10, pady=10)

    def is_alive(self) -> bool:
        return bool(self.frame is not None and self.frame.winfo_exists())

    def auto_import_requested(self) -> bool:
        return bool(self.auto_import.get())

    def update_progress(self, progress) -> None:
        if not self.is_alive():
            return
        value = (
            progress.percentage if isinstance(progress.percentage, (int, float)) else 0
        )
        self.progressbar["value"] = value
        self.status.set(
            self._text(keys.PROGRESS_FORMAT).format(
                str(progress.percentage),
                str(progress.speed),
                str(progress.bytes_downloaded),
                str(progress.file_size),
            )
        )

    def close(self) -> None:
        if self.is_alive():
            self.frame.destroy()

    def show_success(self, *, filename: str, elapsed: float) -> None:
        self.host_window.message_pop(
            self._text(keys.COMPLETE_MESSAGE_FORMAT).format(filename, str(elapsed)),
            "green",
        )

    def show_error(self, message: str) -> None:
        self.host_window.message_pop(message, "red")


__all__ = ["FirmwareDownloadView"]
