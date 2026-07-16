from __future__ import annotations

from src.app.ui_feedback import UiDispatcher
from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.trim_raw_image.service import execute_trim, normalize_path, validate_path


class TrimRawImageController:
    """Schedule raw image trimming and deliver progress to the UI."""

    def __init__(self, *, task_runner: UiTaskRunner, dispatcher: UiDispatcher) -> None:
        self._task_runner = task_runner
        self._dispatcher = dispatcher

    @staticmethod
    def validate(path: str) -> str | None:
        error = validate_path(path)
        return error.value if error is not None else None

    def start(self, path: str, *, on_progress, on_success, on_error) -> None:
        normalized = normalize_path(path)

        def worker():
            return execute_trim(
                normalized,
                progress_callback=lambda value: self._dispatcher.dispatch(on_progress, value),
            )

        self._task_runner.run(worker, on_success=on_success, on_error=on_error, exclusive=True)


__all__ = ['TrimRawImageController']
