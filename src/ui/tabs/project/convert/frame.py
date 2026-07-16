from __future__ import annotations

import logging
from tkinter import BOTH, BOTTOM, Frame, X
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.common.controls import ListBox
from src.ui.common.windowing import Toplevel
from src.ui.warn.dialogs import warn_win
from .presenter import apply_candidate_group, replace_list_items
from .form import build_conversion_header
from .state import ConvertViewState
from . import keys


class FormatConversion(Toplevel):
    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        controller,
        task_runner_factory,
        input_formats: tuple[str, ...],
        output_formats: tuple[str, ...],
        master=None,
    ):
        super().__init__(master=master, center_on_open=False)
        self._texts = texts
        self.title(texts.resolve_required_ui_text(keys.WINDOW_TITLE))
        self.state = ConvertViewState(
            input_formats=input_formats, output_formats=output_formats
        )
        self.controller = controller
        self.frame = None
        self.h = None
        self.f = None
        self.list_b = None
        self.task_runner = task_runner_factory(self)
        self.cancel_button = None
        self.convert_button = None
        self._build()
        self.center_after_layout(force=True)

    def _build(self):
        container = ttk.Frame(self)
        container.pack(padx=10, pady=10, fill=BOTH, expand=True)
        self.frame, self.h, self.f = build_conversion_header(
            container, self.state, on_source_change=self.relist
        )
        self.list_b = ListBox(
            container,
            texts=self._texts,
            set_all_text=self._texts.resolve_required_ui_text(keys.SELECT_ALL_CHECKBOX),
        )
        self.list_b.gui()
        self.list_b.pack(padx=5, pady=5, fill=BOTH, expand=True)
        self._relist(auto_select=True)
        footer = Frame(container)
        self.cancel_button = ttk.Button(
            footer,
            text=self._texts.resolve_required_ui_text(keys.CANCEL_BUTTON),
            command=self.destroy,
        )
        self.cancel_button.pack(side="left", padx=5, pady=5, fill=BOTH, expand=True)
        self.convert_button = ttk.Button(
            footer,
            text=self._texts.resolve_required_ui_text(keys.CONVERT_BUTTON),
            command=self.conversion,
            style="Accent.TButton",
        )
        self.convert_button.pack(side="left", padx=5, pady=5, fill=BOTH, expand=True)
        footer.pack(side=BOTTOM, fill=X)

    def _relist(self, *, auto_select: bool = False):
        source_format = self.h.get()
        if auto_select:
            return self.task_runner.run(
                self.controller.choose_candidate_group,
                source_format,
                on_success=lambda result: apply_candidate_group(
                    self, result or (source_format, [])
                ),
            )
        return self.task_runner.run(
            self.controller.list_candidates,
            source_format,
            on_success=lambda items: replace_list_items(self, items or []),
        )

    def relist(self):
        return self._relist(auto_select=False)

    def _set_busy(self, busy: bool) -> None:
        if not self.winfo_exists():
            return
        state = "disabled" if busy else "normal"
        if self.cancel_button is not None:
            self.cancel_button.configure(state=state)
        if self.convert_button is not None:
            self.convert_button.configure(
                state=state,
                text=(
                    self._texts.resolve_required_ui_text(keys.RUNNING_BUTTON)
                    if busy
                    else self._texts.resolve_required_ui_text(keys.CONVERT_BUTTON)
                ),
            )

    def _handle_conversion_success(self, succeeded: bool) -> None:
        if succeeded:
            self.destroy()
            return
        warn_win(
            texts=self._texts,
            text=self._texts.resolve_required_ui_text(keys.CONVERSION_FAILED_MESSAGE),
            title=self._texts.resolve_required_ui_text(
                keys.CONVERSION_FAILED_DIALOG_TITLE
            ),
            ok=self._texts.resolve_required_ui_text(
                keys.CONVERSION_FAILED_DIALOG_OK_BUTTON
            ),
            master=self,
        )

    def _handle_conversion_error(self, error: Exception) -> None:
        logging.exception("Image conversion failed")
        warn_win(
            texts=self._texts,
            text=str(error),
            title=self._texts.resolve_required_ui_text(
                keys.CONVERSION_ERROR_DIALOG_TITLE
            ),
            ok=self._texts.resolve_required_ui_text(
                keys.CONVERSION_ERROR_DIALOG_OK_BUTTON
            ),
            master=self,
        )

    def conversion(self):
        source_format = self.h.get()
        target_format = self.f.get()
        items = self.list_b.selected.copy()
        if not items:
            warn_win(
                texts=self._texts,
                text=self._texts.resolve_required_ui_text(
                    keys.SELECTION_REQUIRED_MESSAGE
                ),
                title=self._texts.resolve_required_ui_text(
                    keys.SELECTION_REQUIRED_DIALOG_TITLE
                ),
                ok=self._texts.resolve_required_ui_text(
                    keys.SELECTION_REQUIRED_DIALOG_OK_BUTTON
                ),
                master=self,
            )
            return False
        self._set_busy(True)
        return self.task_runner.run(
            self.controller.convert,
            source_format,
            target_format,
            items,
            on_success=self._handle_conversion_success,
            on_error=self._handle_conversion_error,
            on_finally=lambda: self._set_busy(False),
            exclusive=True,
        )
