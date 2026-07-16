from __future__ import annotations

from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner


def build_window_task_runtime(window, *, logger=None):
    dispatcher = build_ui_dispatcher(host_window=window)
    task_runner = build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=window.winfo_exists,
        logger=logger,
    )
    return dispatcher, task_runner


__all__ = ['build_window_task_runtime']
