from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from enum import Enum
from typing import Protocol

from src.platform.process_launcher import launch_detached
from src.core.url_paths import download_filename
from src.platform.git_repository import is_git_available, pull_repository
from src.platform.runtime_directories import ensure_directory
from src.logic.network_downloads import download_api
from src.app.runtime.flags import States

from src.logic.update.install_service import apply_staged_update, build_updater_path, cleanup_completed_update, prepare_update_payload
from src.logic.update.models import PreparedUpdatePayload, UpdateApplyResult, UpdateCleanupResult


class UpdateSettings(Protocol):
    language: str
    oobe: str
    version: str
    version_old: str
    new_tool: str
    wait_pids: str
    update_files: str
    update_done: str

    def set_value(self, name: str, value: object) -> None: ...


class PendingUpdateMode(Enum):
    PREPARE = 'prepare'
    APPLY = 'apply'
    CLEANUP = 'cleanup'


def detect_pending_update_mode(argv_name: str, update_done: str) -> PendingUpdateMode:
    executable_name = os.path.basename(argv_name).lower()
    if executable_name.startswith('tool') and update_done == 'true':
        return PendingUpdateMode.CLEANUP
    if executable_name == 'updater.exe':
        return PendingUpdateMode.APPLY
    return PendingUpdateMode.PREPARE


class UpdateOrchestrator:
    def __init__(
        self,
        *,
        settings: UpdateSettings,
        states: States,
        cwd_path: str,
        temp_path: str,
        tool_self_path: str,
        downloader: Callable[..., Iterable[tuple]] = download_api,
        process_launcher: Callable[[str | list[str]], object] = launch_detached,
        repository_puller: Callable[[str], None] = pull_repository,
    ):
        self.settings = settings
        self.states = states
        self.cwd_path = os.path.normpath(cwd_path)
        self.temp_path = os.path.normpath(temp_path)
        self.tool_self_path = os.path.normpath(tool_self_path)
        self.downloader = downloader
        self.process_launcher = process_launcher
        self.repository_puller = repository_puller

    def can_pull_source_repository(self) -> bool:
        return is_git_available()

    def pull_source_repository(self) -> None:
        self.repository_puller(self.cwd_path)

    def download_and_prepare(
        self,
        download_url: str,
        size: int,
        *,
        on_progress: Callable[[int], None],
        is_cancelled: Callable[[], bool],
    ) -> PreparedUpdatePayload:
        if not download_url:
            raise ValueError('Update download URL is empty')
        ensure_directory(self.temp_path)
        update_zip = os.path.join(self.temp_path, download_filename(download_url))
        for percentage, _speed, _downloaded, _total, _elapsed in self.downloader(
            download_url,
            self.temp_path,
            size_=size,
        ):
            if is_cancelled():
                raise RuntimeError('Update was cancelled')
            if percentage != 'None':
                on_progress(int(percentage))
        on_progress(100)
        return self.prepare_payload(update_zip)

    def prepare_payload(self, update_zip: str) -> PreparedUpdatePayload:
        payload = prepare_update_payload(
            update_zip,
            cwd_path=self.cwd_path,
            temp_path=self.temp_path,
            tool_self_path=self.tool_self_path,
            open_pids=self.states.open_pids,
            language=self.settings.language,
            oobe=self.settings.oobe,
            version=self.settings.version,
            os_name=os.name,
            current_pid=os.getpid(),
        )
        if os.getpid() not in self.states.open_pids:
            self.states.open_pids.append(os.getpid())
        return payload

    def persist_and_launch_updater(self, payload: PreparedUpdatePayload) -> None:
        for key, value in payload.update_dict.items():
            self.settings.set_value(key, value)
        self.process_launcher(payload.updater_path)

    def apply_staged_and_launch(self) -> UpdateApplyResult:
        result = apply_staged_update(
            cwd_path=self.cwd_path,
            temp_path=self.temp_path,
            new_tool=self.settings.new_tool,
            wait_pids=self.settings.wait_pids,
            update_files=self.settings.update_files,
            version_old=self.settings.version_old,
            os_name=os.name,
            current_pid=os.getpid(),
        )
        for key, value in result.settings_updates.items():
            self.settings.set_value(key, value)
        if result.success:
            if not result.launch_path:
                raise RuntimeError('Staged update completed without a launch path')
            self.process_launcher(result.launch_path)
        return result

    def cleanup_completed(self) -> UpdateCleanupResult:
        result = cleanup_completed_update(
            updater_path=build_updater_path(self.cwd_path),
            new_tool=self.settings.new_tool,
            wait_pids=self.settings.wait_pids,
        )
        self.settings.set_value('updating', 'false')
        self.settings.set_value('new_tool', '')
        self.settings.set_value('update_files', '')
        self.settings.set_value('update_done', 'false')
        return result


__all__ = [
    'PendingUpdateMode',
    'UpdateOrchestrator',
    'detect_pending_update_mode',
]
