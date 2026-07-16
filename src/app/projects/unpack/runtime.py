from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.app.runtime.contexts.projects import (
    resolve_current_project_name,
    resolve_project_manager,
)
from src.app.runtime.contexts.settings import resolve_animation, resolve_settings
from src.app.runtime.contexts.ui import (
    resolve_default_message_pop,
    resolve_ui_host_window,
)
from src.app.ui_feedback import (
    UiDispatcher,
    UiNotifier,
    build_ui_dispatcher,
)
from src.app.ui_tasks import UiTaskRunner, build_ui_task_runner
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.projects.unpack.runtime_context import build_workflow_runtime_context


def _host_is_alive(host_window) -> bool:
    if host_window is None:
        return False
    try:
        return bool(host_window.winfo_exists())
    except Exception:
        return False


@dataclass(frozen=True)
class UnpackRuntimeContext:
    current_project_name: object
    project_manager: object
    json_edit_cls: type
    format_bytes_func: Callable
    gettype_func: Callable
    unpack_func: Callable
    notifier: UiNotifier
    animation: object
    open_pack_partitions: Callable
    dispatcher: UiDispatcher

    @property
    def message_pop(self):
        return self.notifier.show


@dataclass(frozen=True)
class UnpackViewRuntimeContext:
    host_window: object
    project_manager: object
    current_project_name: object
    settings: object
    animation: object
    message_pop: Callable[..., Any]
    dispatcher: UiDispatcher
    task_runner: UiTaskRunner
    workflow_runtime: object


def build_unpack_view_runtime_context(
    *,
    host_window=None,
    project_manager=None,
    current_project_name=None,
    settings=None,
    animation=None,
    message_pop=None,
    start_worker=None,
    output: ServiceOutput | None = None,
) -> UnpackViewRuntimeContext:
    resolved_host_window = resolve_ui_host_window(host_window)
    resolved_project_manager = resolve_project_manager(project_manager)
    resolved_current_project_name = resolve_current_project_name(current_project_name)
    resolved_settings = resolve_settings(settings)
    resolved_animation = resolve_animation(animation)
    resolved_message_pop = resolve_default_message_pop(
        message_pop, host_window=resolved_host_window
    )
    if not callable(resolved_message_pop):
        raise RuntimeError("Unpack UI runtime requires message_pop.")
    dispatcher = build_ui_dispatcher(host_window=resolved_host_window)
    task_runner = build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=lambda: _host_is_alive(resolved_host_window),
        start_worker=start_worker,
    )
    workflow_runtime = build_workflow_runtime_context(
        input_path=resolved_project_manager.current_input_path(),
        work_path=resolved_project_manager.current_work_path(),
        output_path=resolved_project_manager.current_work_output_path(),
        project_selected=resolved_project_manager.exist(),
        tool_bin=resolved_settings.tool_bin,
        magisk_not_decompress=resolved_settings.magisk_not_decompress,
        boot_skip_ramdisk=resolved_settings.boot_skip_ramdisk,
        output=output or build_service_output(),
    )
    return UnpackViewRuntimeContext(
        host_window=resolved_host_window,
        project_manager=resolved_project_manager,
        current_project_name=resolved_current_project_name,
        settings=resolved_settings,
        animation=resolved_animation,
        message_pop=resolved_message_pop,
        dispatcher=dispatcher,
        task_runner=task_runner,
        workflow_runtime=workflow_runtime,
    )


__all__ = [
    "UnpackRuntimeContext",
    "UnpackViewRuntimeContext",
    "build_unpack_view_runtime_context",
]
