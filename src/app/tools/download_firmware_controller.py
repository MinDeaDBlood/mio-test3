from __future__ import annotations

from collections.abc import Callable

from src.logic.tools.download_firmware.use_case import DownloadFirmwareUseCase, FirmwareDownloadProgress, FirmwareDownloadResult


class FirmwareDownloadController:
    """Run the firmware download use case and deliver progress through explicit callbacks."""

    def __init__(self, *, output_dir: str, use_case: DownloadFirmwareUseCase, dispatcher, task_runner) -> None:
        self._output_dir = output_dir
        self._use_case = use_case
        self._dispatcher = dispatcher
        self._task_runner = task_runner

    def start(
        self,
        url: str,
        *,
        auto_import: bool | Callable[[], bool],
        on_progress: Callable[[FirmwareDownloadProgress], None],
        on_success: Callable[[FirmwareDownloadResult], None],
        on_error: Callable[[Exception], None],
    ) -> object:
        def worker() -> FirmwareDownloadResult:
            return self._use_case.execute(
                url=url,
                output_dir=self._output_dir,
                auto_import=auto_import,
                on_progress=lambda progress: self._dispatcher.dispatch(on_progress, progress),
            )

        return self._task_runner.run(worker, on_success=on_success, on_error=on_error, exclusive=True)


__all__ = ['FirmwareDownloadController']
