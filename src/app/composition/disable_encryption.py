from __future__ import annotations

import logging

from src.app.composition._ui_task import build_window_task_runtime
from src.app.localization_runtime import lang
from src.app.runtime.contexts.projects import resolve_project_manager
from src.app.tools.disable_encryption_controller import DisableEncryptionController
from src.core.json_store import JsonEdit
from src.ui.tabs.tools.disable_encryption.window import DisableEncryption


def open_disable_encryption_window() -> DisableEncryption:
    window = DisableEncryption(language=lang)
    _, task_runner = build_window_task_runtime(window, logger=logging)
    window.attach(
        controller=DisableEncryptionController(
            project_manager=resolve_project_manager(),
            json_edit_cls=JsonEdit,
            task_runner=task_runner,
        )
    )
    return window


__all__ = ['open_disable_encryption_window']
