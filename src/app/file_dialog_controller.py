from __future__ import annotations

from collections.abc import Callable

from src.app.ui_tasks import UiTaskRunner
from src.core.directory_listing import list_directories, list_matching_files


class FileDialogController:
    def __init__(self, task_runner: UiTaskRunner):
        self._task_runner = task_runner

    def refresh_files(
        self,
        directory: str,
        pattern: str,
        *,
        on_success: Callable[[tuple[str, tuple[str, ...]]], object],
        on_error: Callable[[Exception], object],
    ) -> None:
        self._task_runner.run(
            list_matching_files,
            directory,
            pattern,
            on_success=on_success,
            on_error=on_error,
        )

    def refresh_directories(
        self,
        directory: str,
        *,
        on_success: Callable[[tuple[str, tuple[str, ...]]], object],
        on_error: Callable[[Exception], object],
    ) -> None:
        self._task_runner.run(
            list_directories,
            directory,
            on_success=on_success,
            on_error=on_error,
        )


__all__ = ['FileDialogController']
