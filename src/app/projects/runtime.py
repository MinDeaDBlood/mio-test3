"""Runtime boundary helpers for the primary project workspace UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.app.runtime.contexts.projects import resolve_current_project_name, resolve_project_manager
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import UiDispatcher, UiNotifier, build_ui_dispatcher, build_ui_notifier
from src.app.ui_tasks import UiTaskRunner, build_ui_task_runner


def _host_is_alive(host_window) -> bool:
    if host_window is None:
        return True
    try:
        return bool(host_window.winfo_exists())
    except Exception:
        return False


@dataclass(frozen=True)
class ProjectWorkspaceRuntimeContext:
    host_window: object
    project_manager: object
    current_project_name: object
    notifier: UiNotifier
    dispatcher: UiDispatcher
    task_runner: UiTaskRunner



def build_project_workspace_runtime_context(*, host_window=None, project_manager=None, current_project_name=None, notifier: UiNotifier | None = None, dispatcher: UiDispatcher | None = None, task_runner: UiTaskRunner | None = None, start_worker: Callable[..., Any] | None = None) -> ProjectWorkspaceRuntimeContext:
    resolved_host_window = resolve_ui_host_window(host_window)
    resolved_project_manager = resolve_project_manager(project_manager)
    resolved_current_project_name = resolve_current_project_name(current_project_name)
    dispatcher = dispatcher or build_ui_dispatcher(host_window=resolved_host_window)
    notifier = notifier or build_ui_notifier(host_window=resolved_host_window)
    task_runner = task_runner or build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=lambda: _host_is_alive(resolved_host_window),
        start_worker=start_worker,
    )
    return ProjectWorkspaceRuntimeContext(
        host_window=resolved_host_window,
        project_manager=resolved_project_manager,
        current_project_name=resolved_current_project_name,
        notifier=notifier,
        dispatcher=dispatcher,
        task_runner=task_runner,
    )


__all__ = [
    'ProjectWorkspaceRuntimeContext',
    'build_project_workspace_runtime_context',
]
