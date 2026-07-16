from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import LEFT, X, Frame, StringVar, ttk

from src.ui.common.windowing import Toplevel
from src.ui.contracts import SelinuxAuditAllowControllerPort
from src.ui.tabs.tools.allow_selinux_audit import keys
from src.ui.warn.dialogs import warn_win


class SelinuxAuditAllow(Toplevel):
    def __init__(
        self,
        *,
        language,
        choose_log_file: Callable[[], str],
        choose_output_directory: Callable[[], str],
    ) -> None:
        super().__init__()
        self._language = language
        self._choose_log_file_dialog = choose_log_file
        self._choose_output_directory_dialog = choose_output_directory
        self._controller: SelinuxAuditAllowControllerPort | None = None
        self._completed = False
        self.title(self._text(keys.TITLE))
        self.choose_file = StringVar(value="")
        self.output_dir = StringVar(value="")
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

    def attach(self, *, controller: SelinuxAuditAllowControllerPort) -> None:
        self._controller = controller

    def _require_controller(self) -> SelinuxAuditAllowControllerPort:
        if self._controller is None:
            raise RuntimeError("SelinuxAuditAllowControllerPort is not attached")
        return self._controller

    def _choose_log_file(self) -> None:
        selected = self._choose_log_file_dialog()
        if selected:
            self.choose_file.set(selected)
        self.lift()

    def _choose_output_dir(self) -> None:
        selected = self._choose_output_directory_dialog()
        if selected:
            self.output_dir.set(selected)
        self.lift()

    def _build_ui(self) -> None:
        frame = Frame(self)
        ttk.Label(frame, text=self._text(keys.LOG_FILE_LABEL)).pack(
            side=LEFT,
            fill=X,
            padx=5,
            pady=5,
        )
        ttk.Entry(frame, textvariable=self.choose_file).pack(
            side=LEFT,
            fill=X,
            padx=5,
            pady=5,
        )
        ttk.Button(
            frame,
            text=self._text(keys.LOG_FILE_BROWSE_BUTTON),
            command=self._choose_log_file,
        ).pack(side=LEFT, fill=X, padx=5, pady=5)
        frame.pack(padx=5, pady=5, anchor="nw", fill=X)

        output_frame = Frame(self)
        ttk.Label(output_frame, text=self._text(keys.OUTPUT_DIRECTORY_LABEL)).pack(
            side=LEFT,
            fill=X,
            padx=5,
            pady=5,
        )
        ttk.Entry(output_frame, textvariable=self.output_dir).pack(
            side=LEFT,
            fill=X,
            padx=5,
            pady=5,
        )
        ttk.Button(
            output_frame,
            text=self._text(keys.OUTPUT_DIRECTORY_BROWSE_BUTTON),
            command=self._choose_output_dir,
        ).pack(side=LEFT, fill=X, padx=5, pady=5)
        output_frame.pack(padx=5, pady=5, anchor="nw", fill=X)

        self.button = ttk.Button(
            self,
            text=self._text(keys.RUN_BUTTON),
            command=self.run,
            style="Accent.TButton",
        )
        self.button.pack(padx=5, pady=5, fill=X)

    def _set_running_state(self, running: bool) -> None:
        self.button.configure(
            text=self._text(keys.RUNNING_BUTTON if running else keys.DONE_BUTTON),
            state="disabled" if running else "normal",
            style="Accent.TButton" if running else "",
        )

    def _handle_run_success(self, _result=None) -> None:
        if self.winfo_exists():
            self._completed = True
            self._set_running_state(False)

    def _handle_run_error(self, exc: Exception) -> None:
        logging.exception("SelinuxAuditAllow.run")
        if self.winfo_exists():
            self.button.configure(
                text=self._text(keys.RUN_BUTTON),
                state="normal",
                style="Accent.TButton",
            )
        self._warn(str(exc))

    def _validation_message(self, error_code: str) -> str:
        messages = {
            "log_path_required": self._text(keys.LOG_PATH_REQUIRED_MESSAGE),
            "log_file_not_found": self._text(keys.LOG_FILE_NOT_FOUND_MESSAGE),
            "output_dir_required": self._text(keys.OUTPUT_DIRECTORY_REQUIRED_MESSAGE),
            "output_dir_not_found": self._text(keys.OUTPUT_DIRECTORY_NOT_FOUND_MESSAGE),
        }
        return messages[error_code]

    def run(self) -> None:
        if self._completed:
            self.destroy()
            return
        controller = self._require_controller()
        log_path = self.choose_file.get()
        output_dir = self.output_dir.get()
        validation_error = controller.validate(log_path=log_path, output_dir=output_dir)
        if validation_error is not None:
            self._warn(self._validation_message(validation_error))
            return
        self._set_running_state(True)
        controller.start(
            log_path=log_path,
            output_dir=output_dir,
            on_success=self._handle_run_success,
            on_error=self._handle_run_error,
        )


__all__ = ["SelinuxAuditAllow"]
