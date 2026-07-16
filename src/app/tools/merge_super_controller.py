from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.app.ui_feedback import UiDispatcher
from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.merge_super import MergeSuperRequest, MergeSuperResult, MergeSuperService


@dataclass(frozen=True)
class MergeSuperContext:
    can_run: bool
    project_path: Path | None
    output_path: Path | None


class MergeSuperController:
    """Application controller for the merge-super workflow.

    It owns background execution and delivery of progress/results to the UI.
    The view only gathers input and renders callbacks.
    """

    def __init__(
        self,
        *,
        service: MergeSuperService,
        task_runner: UiTaskRunner,
        dispatcher: UiDispatcher,
    ) -> None:
        self._service = service
        self._task_runner = task_runner
        self._dispatcher = dispatcher

    def context(self) -> MergeSuperContext:
        if not self._service.has_project():
            return MergeSuperContext(can_run=False, project_path=None, output_path=None)
        return MergeSuperContext(
            can_run=True,
            project_path=self._service.current_project_path(),
            output_path=self._service.current_output_path(),
        )

    def start(
        self,
        *,
        output_name: str,
        delete_source: bool,
        on_progress: Callable[[int], None],
        on_success: Callable[[MergeSuperResult], None],
        on_error: Callable[[Exception], None],
        on_finally: Callable[[], None],
    ) -> None:
        request = MergeSuperRequest(output_name=output_name, delete_source=delete_source)

        def worker() -> MergeSuperResult:
            return self._service.execute(
                request,
                progress_callback=lambda value: self._dispatcher.dispatch(on_progress, value),
            )

        self._task_runner.run(
            worker,
            on_success=on_success,
            on_error=on_error,
            on_finally=on_finally,
            exclusive=True,
        )


__all__ = ['MergeSuperContext', 'MergeSuperController']
