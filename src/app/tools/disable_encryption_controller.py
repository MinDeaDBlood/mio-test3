from __future__ import annotations

from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.disable_encryption.service import patch_selected_partitions, scan_project_for_fstab_partitions


class DisableEncryptionController:
    def __init__(self, *, project_manager, json_edit_cls, task_runner: UiTaskRunner) -> None:
        self._project_manager = project_manager
        self._json_edit_cls = json_edit_cls
        self._task_runner = task_runner

    def scan(self):
        if not self._project_manager.exist():
            return ()
        return scan_project_for_fstab_partitions(
            self._project_manager.current_work_path(),
            json_edit_cls=self._json_edit_cls,
        )

    def start_scan(self, *, on_success, on_error) -> None:
        self._task_runner.run(self.scan, on_success=on_success, on_error=on_error)

    def start_patch(self, partitions, selected_partitions, *, on_success, on_error) -> None:
        self._task_runner.run(
            patch_selected_partitions,
            partitions,
            selected_partitions,
            on_success=on_success,
            on_error=on_error,
            exclusive=True,
        )


__all__ = ['DisableEncryptionController']
