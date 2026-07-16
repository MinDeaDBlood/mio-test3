from __future__ import annotations

import platform
from collections.abc import Callable

import tkinter as tk
from tkinter import BOTH, LEFT, RIGHT, TOP, Frame, Text, X
from tkinter import ttk

from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins import module_dialogs_keys as keys


class PluginNewDialog(Toplevel):
    """Collect new-plugin metadata and delegate creation to an app controller."""

    def __init__(
        self,
        controller,
        *,
        texts: LocalizationCatalog,
        open_editor: Callable[[object], object],
        show_info: Callable[[str], object],
        create_gui_on_init: bool = True,
    ):
        super().__init__()
        self._texts = texts
        self.controller = controller
        self.open_editor = open_editor
        self.show_info = show_info
        self.title(self._texts.resolve_required_ui_text(keys.NEW_DIALOG_TITLE))
        if create_gui_on_init:
            self.gui()
            self.center_on_screen(force=True)

    @staticmethod
    def label_entry(master, text, side, value: str = ""):
        frame = Frame(master)
        ttk.Label(frame, text=text).pack(padx=5, pady=5, side=LEFT)
        entry_value = tk.StringVar(value=value)
        ttk.Entry(frame, textvariable=entry_value).pack(padx=5, pady=5, side=RIGHT)
        frame.pack(padx=5, pady=5, fill=X, side=side)
        return entry_value

    def gui(self):
        ttk.Label(
            self,
            text=self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_PLUGIN_CREATE_TITLE),
            font=(None, 25),
        ).pack(fill=BOTH, expand=0, padx=10, pady=10)
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(padx=10, pady=10, fill=X)
        container = ttk.Frame(self)
        fields = ttk.Frame(container)
        self.name = self.label_entry(
            fields, self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_NAME_LABEL), TOP, "example"
        )
        self._default_author = self._texts.resolve_required_ui_text(
            keys.DEFAULT_AUTHOR_VALUE
        )
        self.aou = self.label_entry(
            fields,
            self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_AUTHOR_LABEL),
            TOP,
            self._default_author,
        )
        self.ver = self.label_entry(
            fields, self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_VERSION_LABEL), TOP, "1.0"
        )
        self.dep = self.label_entry(
            fields, self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_REQUIRED_LIBRARIES_LABEL), TOP, ""
        )
        self.identifier = self.label_entry(
            fields,
            self._texts.resolve_required_ui_text(keys.NEW_DIALOG_IDENTIFIER_LABEL),
            TOP,
            "example.mio_kitchen.plugin",
        )
        self.system = self.label_entry(
            fields,
            self._texts.resolve_required_ui_text(
                keys.NEW_DIALOG_SUPPORTED_SYSTEM_LABEL
            ),
            TOP,
            platform.system(),
        )
        self.arch = self.label_entry(
            fields,
            self._texts.resolve_required_ui_text(
                keys.NEW_DIALOG_SUPPORTED_ARCHITECTURE_LABEL
            ),
            TOP,
            platform.machine(),
        )
        fields.pack(padx=5, pady=5, side=LEFT)
        description = ttk.Frame(container)
        ttk.Label(
            description, text=self._texts.resolve_required_ui_text(keys.PLUGINS_MODULE_DIALOGS_DESCRIPTION_LABEL)
        ).pack(padx=5, pady=5, expand=1)
        self.intro = Text(description, width=40, height=15)
        self.intro.pack(fill=BOTH, padx=5, pady=5, side=RIGHT)
        description.pack(padx=5, pady=5, side=LEFT)
        container.pack(padx=5, pady=5)
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(padx=10, pady=10, fill=X)
        ttk.Button(
            self,
            text=self._texts.resolve_required_ui_text(keys.NEW_DIALOG_CREATE_BUTTON),
            command=self.create,
            style="Accent.TButton",
        ).pack(fill=X, padx=5, pady=5)

    def create(self):
        identifier = self.identifier.get().strip()
        if not identifier:
            return
        if self.controller.is_installed(identifier):
            self.show_info(
                self._texts.resolve_required_ui_text(
                    keys.NEW_DIALOG_IDENTIFIER_EXISTS_FORMAT
                )
                % identifier
            )
            return
        data = {
            "name": self.name.get(),
            "author": self.aou.get() or self._default_author,
            "version": self.ver.get(),
            "identifier": identifier,
            "describe": self.intro.get(1.0, tk.END),
            "depend": self.dep.get(),
            "system": self.system.get(),
            "arch": self.arch.get(),
        }
        created_id = self.controller.create_plugin(data)
        target = self.controller.prepare_editor_target(created_id)
        self.destroy()
        self.open_editor(target)


__all__ = ["PluginNewDialog"]
