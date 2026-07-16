from __future__ import annotations

import logging

from src.app.composition._ui_task import build_window_task_runtime
from src.app.composition.dialogs import choose_file
from src.app.localization_runtime import lang
from src.app.tools.trim_raw_image_controller import TrimRawImageController
from src.ui.tabs.tools.trim_raw_image import keys
from src.ui.tabs.tools.trim_raw_image.window import TrimImage


def open_trim_raw_image_window() -> TrimImage:
    text = lang.resolve_required_ui_text
    window = TrimImage(
        language=lang,
        choose_input_file=lambda: choose_file(
            title=text(keys.INPUT_DIALOG_TITLE),
            filetypes=(
                (text(keys.INPUT_DIALOG_IMAGE_FILES), "*.img *.bin"),
                (text(keys.INPUT_DIALOG_ALL_FILES), "*.*"),
            ),
        ),
    )
    dispatcher, task_runner = build_window_task_runtime(window, logger=logging)
    window.attach(
        controller=TrimRawImageController(
            task_runner=task_runner,
            dispatcher=dispatcher,
        )
    )
    return window


__all__ = ["open_trim_raw_image_window"]
