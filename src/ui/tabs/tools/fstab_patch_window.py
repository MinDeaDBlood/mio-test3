from __future__ import annotations

from collections.abc import Callable
from tkinter import BOTH, BOTTOM, LEFT, RIGHT, X, ttk

from src.ui.common.controls import ListBox
from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.warn.dialogs import info_win, warn_win


class FstabPatchWindow(Toplevel):
    """Shared Tk layout for project fstab patch tools.

    Every visible string is supplied by the concrete tool. The shared view does
    not resolve generic localization keys on behalf of different tools.
    """

    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        title: str,
        info_text: str,
        available_partitions_text: str,
        select_all_text: str,
        refresh_text: str,
        run_text: str,
        running_text: str,
        no_partitions_text: str,
        selection_warning: str,
        completion_message: Callable[[int], str],
        warning_dialog_title: str,
        warning_dialog_ok: str,
        completion_dialog_title: str,
        completion_dialog_ok: str,
    ) -> None:
        super().__init__()
        self._texts = texts
        self._controller = None
        self._run_text = run_text
        self._running_text = running_text
        self._no_partitions_text = no_partitions_text
        self._selection_warning = selection_warning
        self._completion_message = completion_message
        self._warning_dialog_title = warning_dialog_title
        self._warning_dialog_ok = warning_dialog_ok
        self._completion_dialog_title = completion_dialog_title
        self._completion_dialog_ok = completion_dialog_ok
        self.partitions = ()
        self.title(title)
        self.minsize(450, 350)

        info_frame = ttk.Frame(self)
        info_frame.pack(padx=10, pady=(10, 5), fill=X)
        ttk.Label(info_frame, text=info_text, wraplength=400).pack(fill=X)

        main_frame = ttk.LabelFrame(self, text=available_partitions_text)
        main_frame.pack(padx=10, pady=5, fill=BOTH, expand=True)
        self.list_box = ListBox(
            main_frame,
            texts=self._texts,
            set_all_text=select_all_text,
        )
        self.list_box.gui()
        self.list_box.pack(padx=5, pady=5, fill=BOTH, expand=True)

        button_frame = ttk.Frame(self)
        button_frame.pack(padx=10, pady=(5, 10), fill=X, side=BOTTOM)
        ttk.Button(
            button_frame,
            text=refresh_text,
            command=self.start_scan_partitions,
        ).pack(side=LEFT, padx=(0, 5))
        self.run_button = ttk.Button(
            button_frame,
            text=run_text,
            style="Accent.TButton",
            command=self.run_patch,
        )
        self.run_button.pack(side=RIGHT, fill=X, expand=True)
        self.center_on_screen(force=True)

    def _warn(self, message: str) -> None:
        warn_win(
            texts=self._texts,
            text=message,
            title=self._warning_dialog_title,
            ok=self._warning_dialog_ok,
            master=self,
        )

    def _inform(self, message: str) -> None:
        info_win(
            message,
            texts=self._texts,
            title=self._completion_dialog_title,
            ok=self._completion_dialog_ok,
            master=self,
        )

    def attach(self, *, controller) -> None:
        self._controller = controller
        self.start_scan_partitions()

    def _require_controller(self):
        if self._controller is None:
            raise RuntimeError("Fstab patch controller is not attached")
        return self._controller

    def start_scan_partitions(self) -> None:
        self.run_button.config(state="disabled", text=self._run_text)
        self._require_controller().start_scan(
            on_success=self._handle_scan_success,
            on_error=lambda exc: self._apply_scan_results((), str(exc)),
        )

    def _handle_scan_success(self, partitions) -> None:
        self._apply_scan_results(partitions)

    def _apply_scan_results(self, partitions, error_message: str | None = None) -> None:
        if not self.winfo_exists():
            return
        self.list_box.clear()
        self.partitions = ()
        if error_message:
            self._warn(error_message)
            self.run_button.config(state="disabled", text=self._run_text)
            return
        self.partitions = tuple(partitions)
        if not self.partitions:
            self._warn(self._no_partitions_text)
            self.run_button.config(state="disabled", text=self._run_text)
            return
        for partition in self.partitions:
            self.list_box.insert(
                f"{partition.name} [{partition.fs_type}]",
                partition.name,
                refresh=False,
            )
        self.list_box.update_ui()
        self.run_button.config(state="normal", text=self._run_text)

    def run_patch(self) -> None:
        selected = tuple(self.list_box.selected)
        if not selected:
            self._warn(self._selection_warning)
            return
        self.run_button.config(state="disabled", text=self._running_text)
        self._require_controller().start_patch(
            self.partitions,
            selected,
            on_success=self._handle_patch_success,
            on_error=self._handle_patch_error,
        )

    def _handle_patch_success(self, modified_count: int) -> None:
        if not self.winfo_exists():
            return
        self.run_button.config(state="normal", text=self._run_text)
        self._inform(self._completion_message(modified_count))
        self.destroy()

    def _handle_patch_error(self, exc: Exception) -> None:
        if not self.winfo_exists():
            return
        self.run_button.config(state="normal", text=self._run_text)
        self._warn(str(exc))


__all__ = ["FstabPatchWindow"]
