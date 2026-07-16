from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import ttk
from tkinter.constants import X

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project import project_menu_keys as keys


class ProjectMenuWidget(ttk.LabelFrame):
    """Project selector view backed by an injected project-menu controller."""

    def __init__(
        self,
        *,
        master,
        texts: LocalizationCatalog,
        current_project_name,
        controller,
        input_func: Callable[..., str],
        open_directory: Callable[[str], object],
        show_message: Callable[..., object],
        emit: Callable[[str], object],
    ):
        super().__init__(master=master, text=texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_PROJECT))
        self._texts = texts
        self.current_project_name = current_project_name
        self.controller = controller
        self.input_func = input_func
        self.open_directory = open_directory
        self.show_message = show_message
        self.emit = emit
        self.combobox: ttk.Combobox

    def open_dir(self):
        try:
            ok, path = self.controller.resolve_current_dir()
            if ok:
                self.open_directory(path)
                return
        except Exception:
            logging.exception("Failed to open project folder")
            path = ""
        self.show_message(
            path
            or self._texts.resolve_required_ui_text(
                keys.OPEN_DIRECTORY_PROJECT_REQUIRED_MESSAGE
            )
        )

    def gui(self):
        self.pack(padx=5, pady=5)
        top_row = ttk.Frame(self)
        top_row.pack(side="top", padx=10, pady=10, fill=X)
        self.combobox = ttk.Combobox(
            top_row, textvariable=self.current_project_name, state="readonly"
        )
        self.combobox.pack(side="left", fill=X, expand=True)
        self.combobox.bind(
            "<<ComboboxSelected>>",
            lambda *_: self.emit(
                self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_SELECTED_ITEMS_LABEL)
                + self.current_project_name.get()
            ),
        )
        ttk.Button(
            top_row,
            text=self._texts.resolve_required_ui_text(keys.BROWSE_BUTTON),
            command=self.open_dir,
        ).pack(side="right", padx=(6, 0))
        for text, command in [
            (self._texts.resolve_required_ui_text(keys.REFRESH_BUTTON), self.listdir),
            (self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_NEW), self.new),
            (self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_DELETE), self.remove),
            (self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_RENAME), self.rename),
        ]:
            ttk.Button(self, text=text, command=command).pack(
                side="left", padx=10, pady=10
            )

    def set_project(self, name):
        if self.controller.project_exists(name):
            self.current_project_name.set(name)

    def listdir(self):
        result = self.controller.refresh_projects()
        projects = list(result.projects)
        self.combobox["value"] = projects
        if not projects:
            self.current_project_name.set("")
            self.combobox.set("")
        elif result.selected_project in projects:
            self.combobox.set(result.selected_project)
        else:
            self.combobox.current(0)

    def rename(self) -> bool:
        name = self.current_project_name.get()
        if not self.controller.project_exists(name):
            self.show_message(
                self._texts.resolve_required_ui_text(
                    keys.RENAME_PROJECT_REQUIRED_MESSAGE
                )
            )
            return False
        target_name = self.input_func(
            texts=self._texts,
            title=self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_RENAME_LABEL) + name,
            text=name,
            master=self.winfo_toplevel(),
        )
        result = self.controller.rename_current(
            target_name,
            exists_message=self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_NAME_CONFLICT),
            unchanged_message=self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_RENAME_UNCHANGED),
            missing_message=self._texts.resolve_required_ui_text(
                keys.RENAME_MISSING_PROJECT_MESSAGE
            ),
        )
        self.combobox["value"] = list(result.projects)
        if not result.succeeded:
            if result.message:
                self.show_message(result.message)
            return False
        self.set_project(result.selected_project)
        return True

    def remove(self):
        result = self.controller.remove_current(
            missing_message=self._texts.resolve_required_ui_text(
                keys.REMOVE_PROJECT_REQUIRED_MESSAGE
            )
        )
        if not result.succeeded and result.message:
            self.show_message(result.message)
        self.combobox["value"] = list(result.projects)
        self.combobox.set(result.selected_project or "")

    def new(self):
        name = self.input_func(texts=self._texts, master=self.winfo_toplevel())
        result = self.controller.create_new(
            name,
            invalid_message=self._texts.resolve_required_ui_text(
                keys.NEW_PROJECT_INVALID_NAME_MESSAGE
            ),
        )
        if not result.succeeded:
            self.show_message(result.message)
        else:
            self.emit(self._texts.resolve_required_ui_text(keys.PROJECT_PROJECT_MENU_WIDGET_NEW_PROJECT_FORMAT) % name)
        self.combobox["value"] = list(result.projects)
        if result.selected_project:
            self.combobox.set(result.selected_project)


__all__ = ["ProjectMenuWidget"]
