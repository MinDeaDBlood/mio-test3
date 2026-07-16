from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import LEFT, X, Frame, StringVar, ttk

from src.ui.common.windowing import Toplevel
from src.ui.contracts import TrimRawImageControllerPort
from src.ui.tabs.tools.trim_raw_image import keys
from src.ui.warn.dialogs import warn_win


class TrimImage(Toplevel):
    def __init__(self, *, language, choose_input_file: Callable[[], str]) -> None:
        super().__init__()
        self._language = language
        self._choose_input_file_dialog = choose_input_file
        self._controller: TrimRawImageControllerPort | None = None
        self._completed = False
        self.title(self._text(keys.TITLE))
        self.choose_file = StringVar(value="")
        self._build_ui()
        self.center_on_screen(force=True)

    def _text(self, key: str) -> str:
        return self._language.resolve_required_ui_text(key)

    def _warn(self, message: str) -> None:
        warn_win(
            texts=self._language,
            text=message,
            title=self._text(keys.WARNING_DIALOG_TITLE),
            ok=self._text(keys.WARNING_DIALOG_OK_BUTTON),
        )

    def attach(self, *, controller: TrimRawImageControllerPort) -> None:
        self._controller = controller

    def _require_controller(self) -> TrimRawImageControllerPort:
        if self._controller is None:
            raise RuntimeError("TrimRawImageControllerPort is not attached")
        return self._controller

    def _choose_input_file(self) -> None:
        selected = self._choose_input_file_dialog()
        if selected:
            self.choose_file.set(selected)
        self.lift()

    def _build_ui(self) -> None:
        ttk.Label(self, text=self._text(keys.DESCRIPTION)).pack(padx=5, pady=5)
        frame = Frame(self)
        ttk.Label(frame, text=self._text(keys.INPUT_LABEL)).pack(
            side=LEFT,
            fill=X,
            padx=5,
            pady=5,
        )
        self.path_edit = ttk.Entry(frame, textvariable=self.choose_file)
        self.path_edit.pack(side=LEFT, fill=X, padx=5, pady=5, expand=True)
        self.choose_button = ttk.Button(
            frame,
            text=self._text(keys.INPUT_BROWSE_BUTTON),
            command=self._choose_input_file,
        )
        self.choose_button.pack(side=LEFT, fill=X, padx=5, pady=5)
        frame.pack(padx=5, pady=5, anchor="nw", fill=X)
        self.button = ttk.Button(
            self,
            text=self._text(keys.RUN_BUTTON),
            command=self.run,
            style="Accent.TButton",
        )
        self.button.pack(padx=5, pady=5, fill=X)

    def _update_progress(self, percentage: int) -> None:
        if self.winfo_exists():
            self.button.configure(
                text=self._text(keys.RUNNING_PROGRESS_FORMAT).format(
                    percentage=percentage
                )
            )

    def _set_running(self, running: bool) -> None:
        if not self.winfo_exists():
            return
        self.button.configure(
            text=self._text(keys.RUNNING_BUTTON if running else keys.DONE_BUTTON),
            state="disabled" if running else "normal",
            style="Accent.TButton" if running else "",
        )
        state = "disabled" if running else "normal"
        self.path_edit.configure(state=state)
        self.choose_button.configure(state=state)

    def run(self) -> None:
        if self._completed:
            self.destroy()
            return
        controller = self._require_controller()
        path = self.choose_file.get()
        validation_error = controller.validate(path)
        if validation_error is not None:
            message_key = (
                keys.PATH_REQUIRED_MESSAGE
                if validation_error == "path_required"
                else keys.PATH_NOT_FOUND_MESSAGE
            )
            self._warn(self._text(message_key))
            return
        self._set_running(True)
        controller.start(
            path,
            on_progress=self._update_progress,
            on_success=self._handle_success,
            on_error=self._handle_error,
        )

    def _handle_success(self, _result=None) -> None:
        self._completed = True
        self._set_running(False)

    def _handle_error(self, exc: Exception) -> None:
        logging.exception("Trim image operation failed")
        self._set_running(False)
        self._warn(str(exc))


__all__ = ["TrimImage"]
