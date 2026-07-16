from __future__ import annotations

import logging

from src.app.composition._ui_task import build_window_task_runtime
from src.app.composition.dialogs import choose_directory, choose_file
from src.app.localization_runtime import lang
from src.app.tools.split_super_controller import SplitSuperController
from src.ui.tabs.tools.split_super.window import SplitSuperWindow
from src.ui.tabs.tools.split_super import keys


def open_split_super_window() -> SplitSuperWindow:
    window = SplitSuperWindow(
        language=lang,
        choose_input_file=lambda: choose_file(
            title=lang.resolve_required_ui_text(keys.INPUT_DIALOG_TITLE)
        ),
        choose_output_directory=lambda: choose_directory(
            title=lang.resolve_required_ui_text(keys.OUTPUT_DIALOG_TITLE)
        ),
    )
    dispatcher, task_runner = build_window_task_runtime(window, logger=logging)
    window.attach(
        controller=SplitSuperController(task_runner=task_runner, dispatcher=dispatcher)
    )
    return window


__all__ = ["open_split_super_window"]
