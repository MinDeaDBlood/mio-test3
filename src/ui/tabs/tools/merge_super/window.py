from __future__ import annotations

import logging
from tkinter import BOTH, LEFT, X, BooleanVar, StringVar, ttk
from typing import Optional

from src.ui.common.windowing import Toplevel
from src.ui.contracts import MergeSuperControllerPort, MergeSuperResultProtocol
from src.ui.tabs.tools.merge_super import keys
from src.ui.tabs.tools.merge_super.presenter import MergeSuperPresenter
from src.ui.warn.dialogs import info_win, warn_win


class MergeSparseImage(Toplevel):
    """Tk view for merging segmented Android sparse image files."""

    def __init__(self, *, language) -> None:
        super().__init__()
        self._language = language
        self._controller: MergeSuperControllerPort | None = None
        self._presenter: MergeSuperPresenter | None = None
        self._can_run = False
        self.title(self._text(keys.TITLE))
        self.minsize(420, 240)
        self.output_filename = StringVar(value="super.img")
        self.delete_source = BooleanVar(value=False)
        self.run_button: Optional[ttk.Button] = None
        self.progressbar: Optional[ttk.Progressbar] = None
        self.progress_label: Optional[ttk.Label] = None

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
            title=self._text(keys.INFORMATION_DIALOG_TITLE),
            ok=self._text(keys.INFORMATION_DIALOG_OK_BUTTON),
        )

    def attach(
        self,
        *,
        controller: MergeSuperControllerPort,
        presenter: MergeSuperPresenter,
    ) -> None:
        self._controller = controller
        self._presenter = presenter
        self._build_ui()
        self.center_on_screen(force=True)

    def _require_controller(self) -> MergeSuperControllerPort:
        if self._controller is None:
            raise RuntimeError("MergeSuperControllerPort is not attached")
        return self._controller

    def _require_presenter(self) -> MergeSuperPresenter:
        if self._presenter is None:
            raise RuntimeError("MergeSuperPresenter is not attached")
        return self._presenter

    def _build_ui(self) -> None:
        controller = self._require_controller()
        presenter = self._require_presenter()
        spec = presenter.build_spec(controller.context())
        self._can_run = spec.can_run
        self.output_filename.set(spec.output_filename)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        ttk.Label(
            main_frame,
            text=self._text(keys.DESCRIPTION),
            wraplength=400,
            justify=LEFT,
        ).pack(pady=(0, 10), fill=X)
        ttk.Label(
            main_frame,
            text=spec.project_path_text,
            foreground="gray",
            wraplength=380,
            justify=LEFT,
        ).pack(pady=(0, 10), fill=X, anchor="w")

        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=X, pady=5)
        ttk.Label(
            output_frame,
            text=self._text(keys.OUTPUT_FILENAME_LABEL),
            width=22,
        ).pack(side=LEFT)
        ttk.Entry(output_frame, textvariable=self.output_filename).pack(
            side=LEFT,
            expand=True,
            fill=X,
        )

        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=X, pady=5)
        ttk.Checkbutton(
            options_frame,
            text=self._text(keys.DELETE_SOURCE_CHECKBOX),
            variable=self.delete_source,
            style="Switch.TCheckbutton",
        ).pack(side=LEFT, pady=5)

        self.run_button = ttk.Button(
            main_frame,
            text=self._text(keys.RUN_BUTTON),
            style="Accent.TButton",
            command=self.start_merge,
        )
        self.run_button.pack(fill=X, pady=(10, 5), ipady=4)
        self.progress_label = ttk.Label(main_frame, text="")
        self.progressbar = ttk.Progressbar(
            main_frame,
            mode="determinate",
            maximum=100,
        )

        if not spec.can_run:
            self.run_button.config(state="disabled")
            ttk.Label(
                main_frame,
                text=self._text(keys.SELECT_PROJECT_MESSAGE),
                foreground="orange",
            ).pack(pady=(5, 0))

    def start_merge(self) -> None:
        presenter = self._require_presenter()
        controller = self._require_controller()
        output_name = self.output_filename.get()
        valid, message = presenter.validate_output_name(
            output_name,
            can_run=self._can_run,
        )
        if not valid:
            self._warn(message)
            return

        self.progress_label.pack(pady=(5, 0))
        self.progressbar.pack(fill=X, pady=(2, 0), expand=True)
        self.update_progress(0)
        controller.start(
            output_name=output_name,
            delete_source=self.delete_source.get(),
            on_progress=self.update_progress,
            on_success=self._apply_process_result,
            on_error=self._handle_process_error,
            on_finally=self._schedule_finish_merge,
        )

    def update_progress(self, percentage: int) -> None:
        if not self.winfo_exists():
            return
        self.run_button.config(state="disabled")
        self.progressbar["value"] = percentage
        self.run_button.config(
            text=self._text(keys.RUNNING_PROGRESS_FORMAT).format(percentage=percentage)
        )

    def _apply_process_result(self, result: MergeSuperResultProtocol) -> None:
        if not self.winfo_exists():
            return
        message_type, message = self._require_presenter().result_message(result)
        if message_type == "warn":
            self._warn(message)
        else:
            self._inform(message)

    def _handle_process_error(self, exc: Exception) -> None:
        logging.exception("Error while merging sparse image segments")
        if self.winfo_exists():
            self.run_button.config(text=self._text(keys.FAILED_BUTTON))
            self.progressbar["value"] = 0
            self._warn(self._require_presenter().unexpected_error_message(exc))

    def _schedule_finish_merge(self) -> None:
        if self.winfo_exists():
            self.after(1500, self.finish_merge)

    def finish_merge(self) -> None:
        if self.winfo_exists():
            self.progressbar.pack_forget()
            self.progress_label.pack_forget()
            self.run_button.config(state="normal", text=self._text(keys.RUN_BUTTON))


__all__ = ["MergeSparseImage"]
