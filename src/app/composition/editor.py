from __future__ import annotations

import logging

from src.app.editor.controller import EditorWindowController
from src.app.localization_runtime import lang
from src.app.composition import editor_keys as keys
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.ui.common.editor.presenter import EditorPresenter
from src.ui.common.editor.window import PythonEditor
from src.ui.common.windowing import Toplevel


def open_editor(directory: str, file_name: str | None = None, *, lexer=None):
    root = Toplevel()
    root.title(lang.resolve_required_ui_text(keys.WINDOW_TITLE))
    dispatcher = build_ui_dispatcher(host_window=root)
    task_runner = build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=root.winfo_exists,
        logger=logging,
    )
    presenter = EditorPresenter(
        controller=EditorWindowController(logger=logging), texts=lang
    )
    editor = PythonEditor(
        root,
        directory,
        file_name,
        texts=lang,
        presenter=presenter,
        task_runner=task_runner,
        lexer=lexer,
    )
    editor.pack(side="top", fill="both", expand=True)
    root.center_on_screen(force=True)
    return root


__all__ = ["open_editor"]
