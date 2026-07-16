from __future__ import annotations

from collections.abc import Callable
from tkinter import BOTH, END, LEFT, X, Listbox, StringVar
from tkinter.ttk import Button, Combobox, Entry, Frame
from typing import Protocol

from src.ui.localization import LocalizationCatalog
from src.ui.common.formatting import enum_value
from src.ui.common.windowing import Toplevel
from src.ui.common import mkc_filedialog_keys as keys


class DialogTargetProtocol(Protocol):
    kind: object
    path: str


class FileSelectionDialog(Toplevel):
    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        title: str,
        filetypes: tuple[tuple[str, str], ...],
        initial_directory: str,
        resolve_activation: Callable[[str, str], DialogTargetProtocol],
        accept_target: Callable[[str, str], str],
        refresh_files: Callable[..., object],
        show_error: Callable[[str], object],
    ) -> None:
        super().__init__()
        self._texts = texts
        self.file = ""
        self._resolve_activation = resolve_activation
        self._accept_target = accept_target
        self._refresh_files = refresh_files
        self._show_error = show_error
        self.title(title)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.type = Combobox(
            self, state="readonly", values=[pattern for _label, pattern in filetypes]
        )
        self.type.current(0)
        self.type.pack(fill=X, padx=5, pady=5)
        self.path = StringVar(value=initial_directory)
        paths = Entry(self, textvariable=self.path)
        paths.bind("<Return>", lambda _event: self.activate_selection())
        paths.pack(fill=X, padx=5, pady=5)
        self.show = Listbox(self, activestyle="dotbox", highlightthickness=0)
        self.show.bind("<Double-Button-1>", lambda _event: self.activate_selection())
        self.show.pack(fill=BOTH, padx=5, pady=5)
        footer = Frame(self)
        Button(
            footer,
            text=self._texts.resolve_required_ui_text(keys.FILE_DIALOG_CHOOSE_BUTTON),
            command=self.accept,
        ).pack(fill=X, side=LEFT, padx=5, pady=5)
        Button(
            footer,
            text=self._texts.resolve_required_ui_text(keys.FILE_DIALOG_REFRESH_BUTTON),
            command=self.refresh_entries,
        ).pack(fill=X, side=LEFT, padx=5, pady=5)
        Button(
            footer,
            text=self._texts.resolve_required_ui_text(keys.FILE_DIALOG_CANCEL_BUTTON),
            command=self.cancel,
        ).pack(fill=X, side=LEFT, padx=5, pady=5)
        footer.pack(padx=5, pady=5, fill=X)

    def selected_name(self) -> str:
        selection = self.show.curselection()
        return self.show.get(selection) if selection else ""

    def activate_selection(self) -> None:
        target = self._resolve_activation(self.path.get(), self.selected_name())
        kind = str(enum_value(target.kind)).strip().lower()
        if kind == "navigate":
            self.path.set(target.path)
            self.refresh_entries()
        elif kind == "select":
            self.file = target.path
            self.destroy()

    def refresh_entries(self) -> None:
        self._refresh_files(
            self.path.get(),
            self.type.get() or "*",
            on_success=self.apply_entries,
            on_error=lambda exc: self._show_error(str(exc)),
        )

    def apply_entries(self, result: tuple[str, tuple[str, ...]]) -> None:
        directory, entries = result
        self.path.set(directory)
        self.show.delete(0, END)
        for entry in entries:
            self.show.insert(END, entry)

    def accept(self) -> None:
        target = self._accept_target(self.path.get(), self.selected_name())
        if target:
            self.file = target
            self.destroy()

    def cancel(self) -> None:
        self.file = ""
        self.destroy()


class DirectorySelectionDialog(Toplevel):
    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        title: str,
        initial_directory: str,
        resolve_activation: Callable[[str, str], DialogTargetProtocol],
        accept_target: Callable[[str, str], str],
        refresh_directories: Callable[..., object],
        show_error: Callable[[str], object],
    ) -> None:
        super().__init__()
        self._texts = texts
        self.file = ""
        self._resolve_activation = resolve_activation
        self._accept_target = accept_target
        self._refresh_directories = refresh_directories
        self._show_error = show_error
        self.title(title)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.path = StringVar(value=initial_directory)
        paths = Entry(self, textvariable=self.path)
        paths.bind("<Return>", lambda _event: self.activate_selection())
        paths.pack(fill=X, padx=5, pady=5)
        self.show = Listbox(self, activestyle="dotbox", highlightthickness=0)
        self.show.bind("<Double-Button-1>", lambda _event: self.activate_selection())
        self.show.pack(fill=BOTH, padx=5, pady=5)
        footer = Frame(self)
        Button(
            footer,
            text=self._texts.resolve_required_ui_text(
                keys.DIRECTORY_DIALOG_CHOOSE_BUTTON
            ),
            command=self.accept,
        ).pack(fill=X, side=LEFT, padx=5, pady=5)
        Button(
            footer,
            text=self._texts.resolve_required_ui_text(
                keys.DIRECTORY_DIALOG_REFRESH_BUTTON
            ),
            command=self.refresh_entries,
        ).pack(fill=X, side=LEFT, padx=5, pady=5)
        Button(
            footer,
            text=self._texts.resolve_required_ui_text(
                keys.DIRECTORY_DIALOG_CANCEL_BUTTON
            ),
            command=self.cancel,
        ).pack(fill=X, side=LEFT, padx=5, pady=5)
        footer.pack(padx=5, pady=5, fill=X)

    def selected_name(self) -> str:
        selection = self.show.curselection()
        return self.show.get(selection) if selection else ""

    def activate_selection(self) -> None:
        target = self._resolve_activation(self.path.get(), self.selected_name())
        kind = str(enum_value(target.kind)).strip().lower()
        if kind == "navigate":
            self.path.set(target.path)
            self.refresh_entries()

    def refresh_entries(self) -> None:
        self._refresh_directories(
            self.path.get(),
            on_success=self.apply_entries,
            on_error=lambda exc: self._show_error(str(exc)),
        )

    def apply_entries(self, result: tuple[str, tuple[str, ...]]) -> None:
        directory, entries = result
        self.path.set(directory)
        self.show.delete(0, END)
        for entry in entries:
            self.show.insert(END, entry)

    def accept(self) -> None:
        target = self._accept_target(self.path.get(), self.selected_name())
        if target:
            self.file = target
            self.destroy()

    def cancel(self) -> None:
        self.file = ""
        self.destroy()


__all__ = ["DirectorySelectionDialog", "DialogTargetProtocol", "FileSelectionDialog"]
