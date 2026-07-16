from __future__ import annotations

from pathlib import Path

from src.app.ui_feedback import UiDispatcher
from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.split_super import (
    SplitSuperRequest,
    execute_split_super,
    validate_split_super_request,
)


class SplitSuperController:
    def __init__(self, *, task_runner: UiTaskRunner, dispatcher: UiDispatcher) -> None:
        self._task_runner = task_runner
        self._dispatcher = dispatcher

    @staticmethod
    def suggest_output_directory(input_path: str) -> str:
        normalized = str(input_path or "").strip()
        if not normalized:
            return ""
        return str(Path(normalized).parent)

    @staticmethod
    def _build_request(
        *,
        input_path: str,
        output_directory: str,
        part_count: int,
        block_size: int,
        suffix_format: str,
        keep_existing: bool,
    ) -> SplitSuperRequest:
        return SplitSuperRequest(
            input_path=input_path,
            output_directory=output_directory,
            part_count=part_count,
            block_size=block_size,
            suffix_format=suffix_format,
            keep_existing=keep_existing,
        )

    def validate(
        self,
        *,
        input_path: str,
        output_directory: str,
        part_count: int,
        block_size: int,
        suffix_format: str,
        keep_existing: bool,
    ) -> None:
        validate_split_super_request(
            self._build_request(
                input_path=input_path,
                output_directory=output_directory,
                part_count=part_count,
                block_size=block_size,
                suffix_format=suffix_format,
                keep_existing=keep_existing,
            )
        )

    def start(
        self,
        *,
        input_path: str,
        output_directory: str,
        part_count: int,
        block_size: int,
        suffix_format: str,
        keep_existing: bool,
        on_progress,
        on_success,
        on_error,
        on_finally,
    ) -> None:
        request = self._build_request(
            input_path=input_path,
            output_directory=output_directory,
            part_count=part_count,
            block_size=block_size,
            suffix_format=suffix_format,
            keep_existing=keep_existing,
        )

        def worker():
            return execute_split_super(
                request,
                progress_callback=lambda value: self._dispatcher.dispatch(
                    on_progress, value
                ),
            )

        self._task_runner.run(
            worker,
            on_success=on_success,
            on_error=on_error,
            on_finally=on_finally,
            exclusive=True,
        )


__all__ = ["SplitSuperController"]
