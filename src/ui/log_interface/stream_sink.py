from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import Text

from src.ui.contracts import StdoutRedirectControllerPort


class StdoutRedirector:
    """Tk text sink.

    Runtime resolution, dispatcher creation and process-stream attachment are
    performed by the application composition root.
    """

    def __init__(
        self,
        text_widget: Text,
        *,
        controller: StdoutRedirectControllerPort,
        suggest_chunks: Callable[[list[str]], None],
        error_popup: Callable[[int, str], None] | None = None,
    ) -> None:
        self.text_space = text_widget
        self.controller = controller
        self._suggest_chunks = suggest_chunks
        self._error_popup = error_popup
        self._closed = False
        self._ui_drain = None
        self._detach_callbacks: list[Callable[[], None]] = []
        try:
            self.text_space.bind('<Destroy>', self._on_destroy, add='+')
        except Exception:
            logging.exception('Unable to bind log sink destruction handler')

    @property
    def data(self):
        return self.controller.data

    def attach_ui_drain(self, drain) -> None:
        if self._ui_drain is not None:
            raise RuntimeError('UI drain is already attached')
        self._ui_drain = drain

    def add_detach_callback(self, callback: Callable[[], None]) -> None:
        self._detach_callbacks.append(callback)

    def replay(self, text: str) -> None:
        if not text or self._closed:
            return
        try:
            self.text_space.insert(tk.END, text)
            self.text_space.see('end')
        except Exception:
            self._on_destroy()

    def _on_destroy(self, *_args) -> None:
        if self._closed:
            return
        self._closed = True
        for detach in self._detach_callbacks:
            try:
                detach()
            except Exception:
                logging.exception('Unable to detach process stream sink')
        self._detach_callbacks.clear()
        if self._ui_drain is not None:
            self._ui_drain.close()

    def is_widget_alive(self) -> bool:
        if self._closed:
            return False
        try:
            return bool(self.text_space.winfo_exists())
        except Exception:
            return False

    def write(self, value) -> None:
        self.controller.write(value)

    def flush(self) -> None:
        if self.controller.request_error_popup() and self._ui_drain is not None:
            self._ui_drain.notify()

    @staticmethod
    def isatty() -> bool:
        return False

    def consume_ui_chunks(self, chunks: list[str]) -> None:
        if self._closed:
            return
        if chunks:
            combined = ''.join(chunks)
            try:
                self.text_space.insert(tk.END, combined)
                self.text_space.see('end')
            except Exception:
                self._on_destroy()
                return
            self._suggest_chunks(chunks)

        error_text = self.controller.consume_error_popup()
        if error_text and self._error_popup is not None:
            try:
                self._error_popup(1, error_text)
            except Exception:
                logging.exception('Error popup failed')


__all__ = ['StdoutRedirector']
