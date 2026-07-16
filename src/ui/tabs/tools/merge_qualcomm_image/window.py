from __future__ import annotations

import logging
from tkinter import StringVar, ttk

from src.ui.common.windowing import Toplevel
from src.ui.contracts import MergeQualcommControllerPort
from src.ui.tabs.tools.merge_qualcomm_image import keys
from src.ui.warn.dialogs import info_win, warn_win


class MergeQualcommImageWindow(Toplevel):
    def __init__(self, *, language, controls) -> None:
        super().__init__()
        self._language = language
        self._controls = controls
        self._controller: MergeQualcommControllerPort | None = None
        self.title(self._text(keys.TITLE))
        self.rawprogram_xml = StringVar()
        self.partition_name = StringVar()
        self.output_path = StringVar()
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

    def _inform(self, message: str) -> None:
        info_win(
            message,
            texts=self._language,
            title=self._text(keys.SUCCESS_DIALOG_TITLE),
            ok=self._text(keys.SUCCESS_DIALOG_OK_BUTTON),
        )

    def attach(self, *, controller: MergeQualcommControllerPort) -> None:
        self._controller = controller

    def _require_controller(self) -> MergeQualcommControllerPort:
        if self._controller is None:
            raise RuntimeError("MergeQualcommControllerPort is not attached")
        return self._controller

    def _build_ui(self) -> None:
        self._controls.filechose(
            self,
            self.rawprogram_xml,
            self._text(keys.RAWPROGRAM_LABEL),
            browse_text=self._text(keys.RAWPROGRAM_BROWSE_BUTTON),
        )
        self._controls.combobox(
            self,
            self.partition_name,
            ("system", "userdata", "cache"),
            self._text(keys.PARTITION_LABEL),
        )
        self._controls.filechose(
            self,
            self.output_path,
            self._text(keys.OUTPUT_DIRECTORY_LABEL),
            is_folder=True,
            browse_text=self._text(keys.OUTPUT_DIRECTORY_BROWSE_BUTTON),
        )
        ttk.Button(
            self,
            text=self._text(keys.RUN_BUTTON),
            command=self.run,
        ).pack(padx=5, pady=5, fill="both")

    def run(self) -> None:
        controller = self._require_controller()
        rawprogram_xml = self.rawprogram_xml.get()
        partition_name = self.partition_name.get()
        output_path = self.output_path.get()
        validation_error = controller.validate(
            rawprogram_xml=rawprogram_xml,
            partition_name=partition_name,
            output_path=output_path,
        )
        if validation_error is not None:
            self._show_validation_error(validation_error)
            return
        controller.start(
            rawprogram_xml=rawprogram_xml,
            partition_name=partition_name,
            output_path=output_path,
            on_success=self._handle_success,
            on_error=self._handle_error,
        )

    def _show_validation_error(self, error_code: str) -> None:
        message_key = (
            keys.RAWPROGRAM_NOT_FOUND_MESSAGE
            if error_code == "rawprogram_not_found"
            else keys.OUTPUT_DIRECTORY_REQUIRED_MESSAGE
        )
        self._warn(self._text(message_key))

    def _handle_success(self, result) -> None:
        if not self.winfo_exists():
            return
        if result.succeeded:
            self.destroy()
            self._inform(self._text(keys.DONE_MESSAGE))
            return
        detail = f"\n{result.details}" if result.details else ""
        self._warn(self._text(keys.FAILURE_MESSAGE_FORMAT).format(detail=detail))

    def _handle_error(self, exc: Exception) -> None:
        logging.error(
            "Merge Qualcomm image operation failed",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        if self.winfo_exists():
            self._warn(str(exc))


__all__ = ["MergeQualcommImageWindow"]
