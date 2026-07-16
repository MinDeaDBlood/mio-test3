from __future__ import annotations

import logging

from src.app.composition._ui_task import build_window_task_runtime
from src.app.composition.dialogs import choose_file
from src.app.localization_runtime import lang
from src.app.runtime.contexts.settings import resolve_settings
from src.app.tools.magisk_patch_controller import MagiskPatchController
from src.core.paths import prog_path
from src.core.random_utils import v_code
from src.logic.projects.common.fs_service import re_folder
from src.app.composition.service_output import build_ui_service_output
from src.ui.tabs.tools.magisk_patch.window import MagiskPatcher
from src.platform.runtime_paths import MAGISK_TEMP_DIR


def open_magisk_patch_window() -> MagiskPatcher:
    window = MagiskPatcher(language=lang, choose_file=choose_file)
    _, task_runner = build_window_task_runtime(window, logger=logging)
    window.attach(
        controller=MagiskPatchController(
            cwd_path=prog_path,
            temp_path=str(MAGISK_TEMP_DIR),
            settings_obj=resolve_settings(),
            v_code_func=v_code,
            re_folder_func=re_folder,
            task_runner=task_runner,
            output=build_ui_service_output(texts=lang),
            logger=logging,
        )
    )
    return window


__all__ = ['open_magisk_patch_window']
