from __future__ import annotations

from tkinter import StringVar, ttk

from src.ui.common.windowing import Toplevel
from src.ui.contracts import DecryptXtcXmlControllerPort
from src.ui.tabs.tools.decrypt_xtc_xml import keys
from src.ui.warn.dialogs import warn_win


class DecryptXtcXml(Toplevel):
    def __init__(self, *, language, controls) -> None:
        super().__init__()
        self._language = language
        self._controls = controls
        self._controller: DecryptXtcXmlControllerPort | None = None
        self.title(self._text(keys.TITLE))
        self.path = StringVar()
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

    def attach(self, *, controller: DecryptXtcXmlControllerPort) -> None:
        self._controller = controller

    def _require_controller(self) -> DecryptXtcXmlControllerPort:
        if self._controller is None:
            raise RuntimeError("DecryptXtcXmlControllerPort is not attached")
        return self._controller

    def _build_ui(self) -> None:
        self._controls.filechose(
            self,
            self.path,
            self._text(keys.PATH_LABEL),
            is_folder=True,
            browse_text=self._text(keys.BROWSE_BUTTON),
        )
        ttk.Button(
            self,
            text=self._text(keys.RUN_BUTTON),
            command=self.run,
        ).pack(padx=5, pady=5, fill="both")

    def run(self) -> None:
        controller = self._require_controller()
        validation_error = controller.validate(self.path.get())
        if validation_error is not None:
            message_key = (
                keys.PATH_REQUIRED_MESSAGE
                if validation_error == "path_required"
                else keys.PATH_NOT_FOUND_MESSAGE
            )
            self._warn(self._text(message_key))
            return
        controller.start(
            self.path.get(),
            on_success=lambda _result: self.destroy() if self.winfo_exists() else None,
            on_error=lambda exc: self._warn(str(exc)),
        )


__all__ = ["DecryptXtcXml"]
