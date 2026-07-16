from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import BOTTOM, LEFT, X, BooleanVar, Frame, StringVar, ttk

from src.ui.contracts import PostInstallConfigControllerPort
from src.ui.localization import LocalizationCatalog
from src.ui.common.controls import input_
from src.ui.common.windowing import Toplevel
from src.ui.tabs.project.pack.postinstall import keys


class PostInstallConfigEditorWindow(Toplevel):
    """Tk editor for postinstall configuration entries."""

    def __init__(
        self,
        *,
        texts: LocalizationCatalog,
        controller: PostInstallConfigControllerPort,
        show_error: Callable[[str], object],
    ) -> None:
        super().__init__()
        self._texts = texts
        self.title(texts.resolve_required_ui_text(keys.TITLE))
        self.controller = controller
        self.show_error = show_error
        try:
            self.entries = self.controller.load()
        except Exception as exc:
            logging.exception("Unable to load postinstall configuration")
            self.show_error(str(exc))
            self.destroy()
            return

        self.post_install_path = StringVar(value="")
        self.filesystem_type = StringVar(value="")
        self.run_postinstall = BooleanVar(value=False)
        self.postinstall_optional = BooleanVar(value=False)
        self._build_ui()
        self._read_selected_entry()
        self.center_on_screen(force=True)

    def _read_selected_entry(self) -> None:
        entry = self.entries.get(self.partition_box.get())
        if entry is None:
            return
        self.run_postinstall.set(entry.run_postinstall)
        self.post_install_path.set(entry.postinstall_path)
        self.filesystem_type.set(entry.filesystem_type)
        self.postinstall_optional.set(entry.postinstall_optional)

    def _store_selected_entry(self) -> None:
        partition = self.partition_box.get()
        if partition not in self.entries:
            return
        self.entries[partition] = self.controller.create_entry(
            partition,
            run_postinstall=bool(self.run_postinstall.get()),
            postinstall_path=self.post_install_path.get(),
            filesystem_type=self.filesystem_type.get(),
            postinstall_optional=bool(self.postinstall_optional.get()),
        )

    def _add_partition(self) -> None:
        partition = input_(
            texts=self._texts,
            title=self._texts.resolve_required_ui_text(keys.NEW_PARTITION_TITLE),
            master=self,
        )
        if not partition:
            return
        try:
            normalized = self.controller.normalize_partition_name(partition)
        except ValueError as exc:
            self.show_error(str(exc))
            return
        self.entries[normalized] = self.controller.create_entry(normalized)
        self.partition_box.config(values=tuple(self.entries))
        self.partition_box.set(normalized)
        self._read_selected_entry()

    def _save(self) -> None:
        self._store_selected_entry()
        try:
            self.controller.save(self.entries.values())
        except Exception as exc:
            logging.exception("Unable to save postinstall configuration")
            self.show_error(str(exc))

    def _build_ui(self) -> None:
        top = Frame(self)
        self.partition_box = ttk.Combobox(top, values=tuple(self.entries))
        self.partition_box.bind(
            "<<ComboboxSelected>>", lambda *_: self._read_selected_entry()
        )
        if self.entries:
            self.partition_box.current(0)
        self.partition_box.pack(padx=5, pady=5, side=LEFT, expand=True, fill=X)
        ttk.Button(top, text="+", command=self._add_partition).pack(
            padx=5, pady=5, side=LEFT, expand=True, fill=X
        )
        ttk.Button(
            top,
            text=self._texts.resolve_required_ui_text(keys.APPLY),
            command=self._store_selected_entry,
        ).pack(padx=5, pady=5, side=LEFT, expand=True, fill=X)

        form = ttk.LabelFrame(
            self, text=self._texts.resolve_required_ui_text(keys.CONFIG)
        )
        self._add_switch(form, "RUN_POSTINSTALL", self.run_postinstall)
        self._add_entry(form, "POSTINSTALL_PATH", self.post_install_path)
        self._add_combobox(
            form, "FILESYSTEM_TYPE", self.filesystem_type, ("ext4", "erofs")
        )
        self._add_switch(form, "POSTINSTALL_OPTIONAL", self.postinstall_optional)
        form.pack(padx=5, pady=5, expand=True, side="top", fill=X)
        top.pack(padx=5, pady=5, expand=True, side="top", fill=X)
        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.SAVE),
            command=self._save,
            style="Accent.TButton",
        ).pack(padx=5, pady=5, expand=True, side=BOTTOM, fill=X)

    @staticmethod
    def _add_switch(master: object, label: str, variable: BooleanVar) -> None:
        frame = Frame(master)
        ttk.Label(frame, text=label).pack(
            padx=5, pady=5, side=LEFT, expand=True, fill=X
        )
        ttk.Checkbutton(
            frame,
            variable=variable,
            onvalue=True,
            offvalue=False,
            style="Switch.TCheckbutton",
        ).pack(padx=5, pady=5, side=LEFT, expand=True, fill=X)
        frame.pack(padx=5, pady=5, expand=True, side="top", fill=X)

    @staticmethod
    def _add_entry(master: object, label: str, variable: StringVar) -> None:
        frame = Frame(master)
        ttk.Label(frame, text=label).pack(
            padx=5, pady=5, side=LEFT, expand=True, fill=X
        )
        ttk.Entry(frame, textvariable=variable).pack(
            padx=5, pady=5, side=LEFT, expand=True, fill=X
        )
        frame.pack(padx=5, pady=5, expand=True, side="top", fill=X)

    @staticmethod
    def _add_combobox(
        master: object, label: str, variable: StringVar, values: tuple[str, ...]
    ) -> None:
        frame = Frame(master)
        ttk.Label(frame, text=label).pack(
            padx=5, pady=5, side=LEFT, expand=True, fill=X
        )
        ttk.Combobox(frame, textvariable=variable, values=values, width=14).pack(
            padx=5, pady=5, side=LEFT, expand=True, fill=X
        )
        frame.pack(padx=5, pady=5, expand=True, side="top", fill=X)


__all__ = ["PostInstallConfigEditorWindow"]
