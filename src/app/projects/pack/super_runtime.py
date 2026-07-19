from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.app.runtime.contexts.projects import resolve_project_manager
from src.app.runtime.contexts.settings import resolve_animation
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner


@dataclass(frozen=True)
class PackSuperWindowRuntime:
    project_manager: Any
    host_window: Any
    work_path: str
    input_path: str
    metadata_path: str
    animation: Any


def build_pack_super_window_runtime() -> PackSuperWindowRuntime:
    project_manager = resolve_project_manager()
    host_window = resolve_ui_host_window()
    return PackSuperWindowRuntime(
        project_manager=project_manager,
        host_window=host_window,
        # Rebuilt images in output have priority.  input is retained as a
        # fallback for partitions that were extracted but not rebuilt.
        work_path=project_manager.current_work_output_path(),
        input_path=project_manager.current_input_path(),
        metadata_path=project_manager.current_work_path(),
        animation=resolve_animation(),
    )


def build_window_task_runner(*, window, logger):
    dispatcher = build_ui_dispatcher(host_window=window)
    return dispatcher, build_ui_task_runner(dispatcher=dispatcher, is_alive=window.winfo_exists, logger=logger)


def build_host_task_runner(*, host_window, logger):
    dispatcher = build_ui_dispatcher(host_window=host_window)
    return dispatcher, build_ui_task_runner(dispatcher=dispatcher, is_alive=host_window.winfo_exists, logger=logger)


def resolve_pack_super_host_window(runtime: PackSuperWindowRuntime | None = None):
    return (runtime or build_pack_super_window_runtime()).host_window


__all__ = [
    'PackSuperWindowRuntime',
    'build_host_task_runner',
    'build_pack_super_window_runtime',
    'build_window_task_runner',
    'resolve_pack_super_host_window',
]
