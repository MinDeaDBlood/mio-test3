from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import BOTH, LEFT, X, BooleanVar, IntVar, StringVar, ttk

from src.ui.common.windowing import Toplevel
from src.ui.contracts import SplitSuperControllerPort, SplitSuperResultProtocol
from src.ui.tabs.tools.split_super import keys
from src.ui.warn.dialogs import info_win, warn_win


class SplitSuperWindow(Toplevel):
    def __init__(
        self,
        *,
        language,
        choose_input_file: Callable[[], str],
        choose_output_directory: Callable[[], str],
    ) -> None:
        super().__init__()
        self._language = language
        self._choose_input_file_dialog = choose_input_file
        self._choose_output_directory_dialog = choose_output_directory
        self._controller = None
        self.input_path = StringVar(value="")
        self.output_directory = StringVar(value="")
        self.part_count = IntVar(value=15)
        self.block_size = StringVar(value="4096")
        self.suffix_format = StringVar(value=".%03d")
        self.keep_existing = BooleanVar(value=False)
        self.title(self._text(keys.TITLE))
        self.minsize(620, 340)
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

    def attach(self, *, controller: SplitSuperControllerPort) -> None:
        self._controller = controller

    def _require_controller(self):
        if self._controller is None:
            raise RuntimeError("SplitSuperController is not attached")
        return self._controller

    def _build_path_row(
        self,
        parent,
        label: str,
        browse_text: str,
        variable: StringVar,
        command,
    ) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=4)
        ttk.Label(frame, text=label, width=22).pack(side=LEFT)
        ttk.Entry(frame, textvariable=variable).pack(
            side=LEFT,
            fill=X,
            expand=True,
            padx=5,
        )
        ttk.Button(frame, text=browse_text, command=command).pack(side=LEFT)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=BOTH, expand=True)
        self._build_path_row(
            root,
            self._text(keys.INPUT_LABEL),
            self._text(keys.INPUT_BROWSE_BUTTON),
            self.input_path,
            self._choose_input,
        )
        self._build_path_row(
            root,
            self._text(keys.OUTPUT_LABEL),
            self._text(keys.OUTPUT_BROWSE_BUTTON),
            self.output_directory,
            self._choose_output,
        )
        options = ttk.Frame(root)
        options.pack(fill=X, pady=8)
        ttk.Label(options, text=self._text(keys.PARTS_LABEL)).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Spinbox(
            options,
            from_=2,
            to=9999,
            textvariable=self.part_count,
            width=8,
        ).grid(row=0, column=1, padx=(5, 16))
        ttk.Label(options, text=self._text(keys.BLOCK_SIZE_LABEL)).grid(
            row=0,
            column=2,
            sticky="w",
        )
        ttk.Entry(options, textvariable=self.block_size, width=10).grid(
            row=0,
            column=3,
            padx=(5, 16),
        )
        ttk.Label(options, text=self._text(keys.SUFFIX_LABEL)).grid(
            row=0,
            column=4,
            sticky="w",
        )
        ttk.Entry(options, textvariable=self.suffix_format, width=12).grid(
            row=0,
            column=5,
            padx=(5, 0),
        )
        ttk.Checkbutton(
            root,
            text=self._text(keys.KEEP_EXISTING_CHECKBOX),
            variable=self.keep_existing,
            style="Switch.TCheckbutton",
        ).pack(anchor="w", pady=5)
        self.progress = ttk.Progressbar(root, maximum=100, mode="determinate")
        self.progress.pack(fill=X, pady=8)
        self.run_button = ttk.Button(
            root,
            text=self._text(keys.RUN_BUTTON),
            style="Accent.TButton",
            command=self.run,
        )
        self.run_button.pack(fill=X, pady=5, ipady=3)

    def _choose_input(self) -> None:
        selected = self._choose_input_file_dialog()
        if selected:
            self.input_path.set(selected)
            if not self.output_directory.get():
                self.output_directory.set(
                    self._require_controller().suggest_output_directory(selected)
                )
        self.lift()

    def _choose_output(self) -> None:
        selected = self._choose_output_directory_dialog()
        if selected:
            self.output_directory.set(selected)
        self.lift()

    def _numeric_values(self) -> tuple[int, int]:
        try:
            block_size = int(self.block_size.get().strip())
            part_count = int(self.part_count.get())
        except ValueError as exc:
            raise ValueError(self._text(keys.NUMERIC_ERROR_MESSAGE)) from exc
        return part_count, block_size

    def run(self) -> None:
        controller = self._require_controller()
        try:
            part_count, block_size = self._numeric_values()
            controller.validate(
                input_path=self.input_path.get(),
                output_directory=self.output_directory.get(),
                part_count=part_count,
                block_size=block_size,
                suffix_format=self.suffix_format.get(),
                keep_existing=self.keep_existing.get(),
            )
        except Exception as exc:
            self._warn(str(exc))
            return
        self._set_running(True)
        controller.start(
            input_path=self.input_path.get(),
            output_directory=self.output_directory.get(),
            part_count=part_count,
            block_size=block_size,
            suffix_format=self.suffix_format.get(),
            keep_existing=self.keep_existing.get(),
            on_progress=self._update_progress,
            on_success=self._handle_success,
            on_error=self._handle_error,
            on_finally=lambda: self._set_running(False),
        )

    def _set_running(self, running: bool) -> None:
        if not self.winfo_exists():
            return
        self.run_button.configure(
            state="disabled" if running else "normal",
            text=self._text(keys.RUNNING_BUTTON if running else keys.RUN_BUTTON),
        )

    def _update_progress(self, value: int) -> None:
        if self.winfo_exists():
            self.progress["value"] = value

    def _handle_success(self, result: SplitSuperResultProtocol) -> None:
        if not self.winfo_exists():
            return
        self.progress["value"] = 100
        self._inform(
            self._text(keys.SUCCESS_MESSAGE).format(
                count=len(result.output_paths),
                directory=result.output_paths[0].parent,
            )
        )

    def _handle_error(self, exc: Exception) -> None:
        logging.exception("Split super operation failed")
        if self.winfo_exists():
            self.progress["value"] = 0
            self._warn(str(exc))


__all__ = ["SplitSuperWindow"]
