from __future__ import annotations

from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.decrypt_xtc_xml.service import decrypt_tree, normalize_path, validate_path


class DecryptXtcXmlController:
    """Schedule XTC XML decryption without owning validation text or widgets."""

    def __init__(self, *, task_runner: UiTaskRunner) -> None:
        self._task_runner = task_runner

    @staticmethod
    def validate(path: str) -> str | None:
        error = validate_path(path)
        return error.value if error is not None else None

    def start(self, path: str, *, on_success, on_error) -> None:
        self._task_runner.run(
            decrypt_tree,
            normalize_path(path),
            on_success=on_success,
            on_error=on_error,
        )


__all__ = ['DecryptXtcXmlController']
