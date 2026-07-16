from __future__ import annotations

from src.ui.tabs.project import action_panel_keys as keys
from collections.abc import Callable
from tkinter import ttk

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project.action_panel_presenter import ProjectActionPanelController


class ProjectActionPanelWidget(ttk.LabelFrame):
    def __init__(
        self,
        *,
        master,
        texts: LocalizationCatalog,
        pack_zip,
        pack_super,
        open_notepad,
        open_convert,
        run_background: Callable[[Callable], object],
    ):
        super().__init__(master=master, text=texts.resolve_required_ui_text(keys.PROJECT_ACTION_PANEL_WIDGET_OTHER))
        self._texts = texts
        self.run_background = run_background
        self.controller = ProjectActionPanelController(
            pack_zip=pack_zip,
            pack_super=pack_super,
            open_notepad=open_notepad,
            open_convert=open_convert,
        )

    def gui(self):
        self.pack(padx=5, pady=5)
        actions = self.controller.build_action_specs(lang=self._texts)
        for column in range(4):
            self.columnconfigure(column, weight=0)

        row = 0
        for index, action in enumerate(actions):
            column = index % 4
            if not column:
                row += 1
            command = (
                (lambda fn=action.command: self.run_background(fn))
                if action.threaded
                else action.command
            )
            width_kwargs = {"width": action.width} if action.width is not None else {}
            ttk.Button(
                self,
                text=action.text,
                command=command,
                **width_kwargs,
            ).grid(
                row=row,
                column=column,
                padx=5,
                pady=5,
                sticky="ew",
            )


__all__ = ["ProjectActionPanelWidget"]
