from __future__ import annotations

from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.allow_selinux_audit.models import SelinuxAuditAllowRequest
from src.logic.tools.allow_selinux_audit.service import (
    build_request,
    execute_request,
    validate_request,
)


class SelinuxAuditAllowController:
    """Application boundary for the SELinux audit conversion workflow."""

    def __init__(self, *, task_runner: UiTaskRunner) -> None:
        self._task_runner = task_runner

    @staticmethod
    def _build_request(*, log_path: str, output_dir: str) -> SelinuxAuditAllowRequest:
        return build_request(log_path=log_path, output_dir=output_dir)

    def validate(self, *, log_path: str, output_dir: str) -> str | None:
        error = validate_request(self._build_request(log_path=log_path, output_dir=output_dir))
        return error.value if error is not None else None

    def start(self, *, log_path: str, output_dir: str, on_success, on_error) -> None:
        request = self._build_request(log_path=log_path, output_dir=output_dir)
        self._task_runner.run(
            execute_request,
            request,
            on_success=on_success,
            on_error=on_error,
        )


__all__ = ['SelinuxAuditAllowController']
