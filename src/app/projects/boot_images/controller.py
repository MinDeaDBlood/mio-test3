from __future__ import annotations

from collections.abc import Callable

from src.app.operation_gate import OperationBusyError
from src.app.ui_tasks import UiTaskRunner
from src.logic.projects.boot_images.runtime_context import BootImageRuntimeContext


class BootImageActionController:
    def __init__(
        self,
        *,
        runtime: BootImageRuntimeContext,
        task_runner: UiTaskRunner,
        operation: Callable[..., object],
    ) -> None:
        self._runtime = runtime
        self._task_runner = task_runner
        self._operation = operation

    def run(self, mode: str) -> None:
        normalized = str(mode or '').strip()
        if normalized not in {'boot', 'recovery', 'vendor_boot'}:
            raise ValueError(f'Unsupported boot image mode: {mode!r}')
        self._task_runner.fire_and_forget(
            self._operation,
            normalized,
            self._runtime,
            on_busy=lambda: self._runtime.output.report(str(OperationBusyError())),
            exclusive=True,
        )


__all__ = ['BootImageActionController']
