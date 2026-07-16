from __future__ import annotations

import logging

from src.app.composition._ui_task import build_window_task_runtime
from src.app.localization_runtime import lang
from src.app.runtime.contexts.projects import resolve_project_manager
from src.app.tools.disable_avb_controller import DisableAvbController
from src.core.json_store import JsonEdit
from src.ui.tabs.tools.disable_avb_in_fstab.window import DisableAVB


def open_disable_avb_window() -> DisableAVB:
    window = DisableAVB(language=lang)
    _, task_runner = build_window_task_runtime(window, logger=logging)
    window.attach(
        controller=DisableAvbController(
            project_manager=resolve_project_manager(),
            json_edit_cls=JsonEdit,
            task_runner=task_runner,
        )
    )
    return window


__all__ = ['open_disable_avb_window']
