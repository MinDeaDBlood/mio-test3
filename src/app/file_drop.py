from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable

from src.platform.filesystem import is_directory, is_file, path_exists
from src.app.composition.project_import import build_project_import_controller
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.core.file_types import gettype


@dataclass(frozen=True)
class InputPathDispatchResult:
    """Synchronous routing result for paths supplied by CLI or drag and drop."""

    missing_paths: tuple[str, ...] = ()
    ignored_paths: tuple[str, ...] = ()


def _open_plugin_installer(path: str):
    from src.app.composition.plugin_installer import open_plugin_installer

    return open_plugin_installer(path)


def _open_generic_file_editor(path: str):
    from src.app.composition.editor import open_editor

    return open_editor(os.path.dirname(path), os.path.basename(path))


def _host_task_runner():
    host_window = resolve_ui_host_window()
    dispatcher = build_ui_dispatcher(host_window=host_window)
    is_alive = host_window.winfo_exists
    return build_ui_task_runner(dispatcher=dispatcher, is_alive=is_alive, logger=logging)


def normalize_input_path(path: str) -> str:
    normalized = path
    if normalized.endswith('}') and normalized.startswith('{'):
        normalized = normalized[1:-1]
    if hasattr(normalized, 'decode'):
        normalized = normalized.decode('gbk')
    return normalized


def handle_input_paths(files: Iterable[str]) -> InputPathDispatchResult:
    """Route supplied paths without formatting or displaying user messages."""

    task_runner = _host_task_runner()
    import_controller = build_project_import_controller()
    missing_paths: list[str] = []
    ignored_paths: list[str] = []

    for item in files:
        path = normalize_input_path(item)
        if not path:
            continue
        if not path_exists(path):
            missing_paths.append(path)
            continue
        if is_file(path):
            if path.endswith('.mpk'):
                _open_plugin_installer(path)
            elif gettype(path) == 'unknown':
                _open_generic_file_editor(path)
            else:
                task_runner.fire_and_forget(lambda source=path: import_controller.import_file(source))
        elif is_directory(path):
            task_runner.fire_and_forget(lambda source=path: import_controller.import_path(source))
        else:
            ignored_paths.append(path)

    return InputPathDispatchResult(
        missing_paths=tuple(missing_paths),
        ignored_paths=tuple(ignored_paths),
    )


__all__ = ['InputPathDispatchResult', 'handle_input_paths', 'normalize_input_path']
