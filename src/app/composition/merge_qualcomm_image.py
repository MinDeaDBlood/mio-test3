from __future__ import annotations

import logging

from src.app.composition._ui_task import build_window_task_runtime
from src.app.composition.dialogs import choose_directory, choose_file
from src.app.localization_runtime import lang
from src.app.tools.merge_qualcomm_controller import MergeQualcommController
from src.ui.common.windowing import CustomControls
from src.ui.tabs.tools.merge_qualcomm_image import keys
from src.ui.tabs.tools.merge_qualcomm_image.window import MergeQualcommImageWindow


def open_merge_qualcomm_image_window() -> MergeQualcommImageWindow:
    text = lang.resolve_required_ui_text
    window = MergeQualcommImageWindow(
        language=lang,
        controls=CustomControls(
            texts=lang,
            choose_file=lambda: choose_file(
                title=text(keys.RAWPROGRAM_DIALOG_TITLE),
                filetypes=(
                    (text(keys.RAWPROGRAM_DIALOG_XML_FILES), "*.xml"),
                    (text(keys.RAWPROGRAM_DIALOG_ALL_FILES), "*.*"),
                ),
            ),
            choose_directory=lambda: choose_directory(
                title=text(keys.OUTPUT_DIRECTORY_DIALOG_TITLE)
            ),
        ),
    )
    _, task_runner = build_window_task_runtime(window, logger=logging)
    window.attach(controller=MergeQualcommController(task_runner=task_runner))
    return window


__all__ = ["open_merge_qualcomm_image_window"]
