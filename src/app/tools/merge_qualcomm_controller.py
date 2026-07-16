from __future__ import annotations

from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.merge_qualcomm_image.models import MergeQualcommRequest
from src.logic.tools.merge_qualcomm_image.service import execute_merge, validate_request


class MergeQualcommController:
    """Application boundary for Qualcomm image merging."""

    def __init__(self, *, task_runner: UiTaskRunner) -> None:
        self._task_runner = task_runner

    @staticmethod
    def _build_request(*, rawprogram_xml: str, partition_name: str, output_path: str) -> MergeQualcommRequest:
        return MergeQualcommRequest(
            rawprogram_xml=str(rawprogram_xml or '').strip(),
            partition_name=str(partition_name or '').strip(),
            output_path=str(output_path or '').strip(),
        )

    def validate(self, *, rawprogram_xml: str, partition_name: str, output_path: str) -> str | None:
        error = validate_request(
            self._build_request(
                rawprogram_xml=rawprogram_xml,
                partition_name=partition_name,
                output_path=output_path,
            )
        )
        return error.value if error is not None else None

    def start(
        self,
        *,
        rawprogram_xml: str,
        partition_name: str,
        output_path: str,
        on_success,
        on_error,
    ) -> None:
        request = self._build_request(
            rawprogram_xml=rawprogram_xml,
            partition_name=partition_name,
            output_path=output_path,
        )
        self._task_runner.run(
            execute_merge,
            request,
            on_success=on_success,
            on_error=on_error,
            exclusive=True,
        )


__all__ = ['MergeQualcommController']
