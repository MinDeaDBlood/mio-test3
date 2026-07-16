from __future__ import annotations

import logging

from src.app.localization_runtime import lang
from src.app.runtime.contexts.projects import resolve_project_manager
from src.app.runtime.contexts.settings import resolve_settings
from src.app.tools.merge_super_controller import MergeSuperController
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.logic.tools.merge_super import MergeSuperService
from src.ui.tabs.tools.merge_super.presenter import MergeSuperPresenter
from src.ui.tabs.tools.merge_super.window import MergeSparseImage


def open_merge_super_window() -> MergeSparseImage:
    window = MergeSparseImage(language=lang)
    dispatcher = build_ui_dispatcher(host_window=window)
    task_runner = build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=window.winfo_exists,
        logger=logging,
    )
    settings = resolve_settings()
    service = MergeSuperService(
        project_manager=resolve_project_manager(),
        tool_bin_path=settings.tool_bin,
    )
    controller = MergeSuperController(
        service=service,
        task_runner=task_runner,
        dispatcher=dispatcher,
    )
    presenter = MergeSuperPresenter(language=lang)
    window.attach(controller=controller, presenter=presenter)
    return window


__all__ = ['open_merge_super_window']
