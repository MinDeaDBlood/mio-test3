from __future__ import annotations

import logging
import platform
import sys
from dataclasses import dataclass
from typing import Callable, Literal

from src.app.update_orchestrator import PendingUpdateMode, UpdateOrchestrator, detect_pending_update_mode
from src.logic.update.models import (
    PreparedUpdatePayload,
    ReleaseAssetSelection,
    ReleaseCheckResult,
    UpdateApplyResult,
    UpdateCleanupResult,
)
from src.logic.update.service import select_release_asset


@dataclass(frozen=True)
class UpdateCheckOutcome:
    release: ReleaseCheckResult
    selection: ReleaseAssetSelection


@dataclass(frozen=True)
class PendingUpdateOutcome:
    mode: Literal["apply", "cleanup"]
    result: UpdateApplyResult | UpdateCleanupResult


class UpdateWorkflowController:
    """Run update use cases without depending on updater widgets or localized text."""

    def __init__(
        self,
        *,
        settings,
        states,
        orchestrator: UpdateOrchestrator,
        task_runner,
        dispatcher,
        update_url: str,
        fetch_release: Callable[[str], ReleaseCheckResult],
        system_name: Callable[[], str] = platform.system,
        machine_name: Callable[[], str] = platform.machine,
        executable_path: Callable[[], str] = lambda: sys.argv[0],
        logger=logging,
    ) -> None:
        self.settings = settings
        self.states = states
        self.orchestrator = orchestrator
        self.task_runner = task_runner
        self.dispatcher = dispatcher
        self.update_url = update_url
        self.fetch_release = fetch_release
        self.system_name = system_name
        self.machine_name = machine_name
        self.executable_path = executable_path
        self.logger = logger
        self.selection = ReleaseAssetSelection(package_name='')

    def request_check(self, *, on_success, on_error) -> None:
        self.task_runner.run(self._check_release, on_success=on_success, on_error=on_error)

    def _check_release(self) -> UpdateCheckOutcome:
        release = self.fetch_release(self.update_url)
        selection = ReleaseAssetSelection(package_name='')
        if release.has_update and release.new_version:
            selection = select_release_asset(
                release.new_version,
                release.assets,
                system_name=self.system_name(),
                machine_name=self.machine_name(),
            )
        self.selection = selection
        return UpdateCheckOutcome(release=release, selection=selection)

    def request_install(
        self,
        *,
        on_progress,
        is_cancelled,
        on_success,
        on_error,
    ) -> None:
        if self.states.run_source:
            self.task_runner.run(
                self.orchestrator.pull_source_repository,
                on_success=lambda _result: on_success(None),
                on_error=on_error,
            )
            return
        if not self.selection.found:
            raise RuntimeError('Update asset is not selected')

        def worker() -> PreparedUpdatePayload:
            return self.orchestrator.download_and_prepare(
                self.selection.download_url,
                self.selection.size,
                on_progress=lambda value: self.dispatcher.dispatch(on_progress, value),
                is_cancelled=is_cancelled,
            )

        self.task_runner.run(worker, on_success=on_success, on_error=on_error)

    def persist_and_launch(self, payload: PreparedUpdatePayload) -> None:
        self.orchestrator.persist_and_launch_updater(payload)

    def request_pending(self, *, on_success, on_error) -> None:
        self.task_runner.run(self._run_pending, on_success=on_success, on_error=on_error)

    def _run_pending(self) -> PendingUpdateOutcome:
        mode = detect_pending_update_mode(self.executable_path(), self.settings.update_done)
        if mode is PendingUpdateMode.APPLY:
            return PendingUpdateOutcome("apply", self.orchestrator.apply_staged_and_launch())
        if mode is PendingUpdateMode.CLEANUP:
            return PendingUpdateOutcome("cleanup", self.orchestrator.cleanup_completed())
        raise RuntimeError('Pending update preparation requires an explicit update archive')

    def recover_pending_failure(self) -> None:
        self.settings.set_value('updating', 'false')
        if self.settings.version_old:
            self.settings.set_value('version', self.settings.version_old)


__all__ = ['PendingUpdateOutcome', 'UpdateCheckOutcome', 'UpdateWorkflowController']
