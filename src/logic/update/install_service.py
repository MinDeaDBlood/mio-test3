from __future__ import annotations

import os
import shutil
import zipfile
from collections.abc import Callable, Iterable
from pathlib import Path

from src.core.process_runner import terminate_process as _terminate_process

from .models import PreparedUpdatePayload, UpdateApplyResult, UpdateCleanupResult


def build_tool_binary_name(*, os_name: str | None = None) -> str:
    """Return the launch binary name used by the existing updater contract."""
    effective_os_name = os_name or os.name
    return 'tool' + ('' if effective_os_name != 'nt' else '.exe')


def build_updater_path(cwd_path: str) -> str:
    return os.path.normpath(os.path.join(cwd_path, 'updater.exe'))


def _split_space_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item for item in str(value).split(' ') if item]


def _terminate_pids(
    pids: Iterable[int | str],
    *,
    terminate_process_func: Callable[[int], object] = _terminate_process,
) -> None:
    for pid in pids:
        try:
            terminate_process_func(int(pid))
        except ProcessLookupError:
            continue


def _safe_relative_zip_member(member_name: str) -> str:
    """Normalize a zip member to a safe relative path.

    ``zipfile.extract`` performs some sanitization itself, but the updater is a
    privileged filesystem operation. Keeping the normalization explicit prevents
    future refactors from accidentally allowing absolute paths or ``..`` escapes.
    """
    normalized = os.path.normpath(member_name).replace('\\', '/')
    if normalized in ('', '.'):
        raise ValueError(f'Invalid update archive member: {member_name!r}')
    drive_or_root = normalized.split('/', 1)[0]
    if normalized.startswith('/') or normalized.startswith('../') or normalized == '..' or ':' in drive_or_root:
        raise ValueError(f'Unsafe update archive member: {member_name!r}')
    return normalized


def _extract_member(zip_ref: zipfile.ZipFile, member_name: str, target_root: str) -> None:
    relative_name = _safe_relative_zip_member(member_name)
    target = Path(target_root) / relative_name
    if member_name.endswith('/'):
        target.mkdir(parents=True, exist_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with zip_ref.open(member_name) as source, target.open('wb') as destination:
        shutil.copyfileobj(source, destination)


def prepare_update_payload(
    update_zip: str,
    *,
    cwd_path: str,
    temp_path: str,
    tool_self_path: str,
    open_pids: Iterable[int | str],
    language: str,
    oobe: str,
    version: str,
    os_name: str | None = None,
    current_pid: int | None = None,
    terminate_process_func: Callable[[int], object] = _terminate_process,
) -> PreparedUpdatePayload:
    """Extract an update package and build the persisted updater settings.

    This function is intentionally UI/runtime-context free. The app layer supplies
    all paths and current settings, then persists the returned ``update_dict``.
    """
    open_pids_list = [str(pid) for pid in open_pids]
    _terminate_pids(open_pids_list, terminate_process_func=terminate_process_func)
    current_pid = os.getpid() if current_pid is None else current_pid
    tool_name = build_tool_binary_name(os_name=os_name)
    update_files: list[str] = []
    with zipfile.ZipFile(update_zip, 'r') as zip_ref:
        for member_name in zip_ref.namelist():
            relative_name = _safe_relative_zip_member(member_name)
            if relative_name == tool_name:
                _extract_member(zip_ref, member_name, os.path.join(cwd_path, 'bin'))
                continue
            try:
                _extract_member(zip_ref, member_name, cwd_path)
            except PermissionError:
                _extract_member(zip_ref, member_name, temp_path)
                if not member_name.endswith('/'):
                    update_files.append(relative_name)
    wait_pids = list(open_pids_list)
    wait_pids.append(str(current_pid))
    updater_path = build_updater_path(cwd_path)
    shutil.copy(tool_self_path, updater_path)
    update_dict = {
        'updating': 'true',
        'language': language,
        'oobe': oobe,
        'new_tool': os.path.join(cwd_path, 'bin', tool_name),
        'version_old': version,
        'update_files': ' '.join(update_files),
        'wait_pids': ' '.join(wait_pids),
    }
    return PreparedUpdatePayload(update_dict=update_dict, updater_path=updater_path)


def apply_staged_update(
    *,
    cwd_path: str,
    temp_path: str,
    new_tool: str | None,
    wait_pids: str | None,
    update_files: str | None,
    version_old: str | None,
    os_name: str | None = None,
    current_pid: int | None = None,
    terminate_process_func: Callable[[int], object] = _terminate_process,
) -> UpdateApplyResult:
    """Apply files staged by the updater helper and return UI/app actions."""
    _terminate_pids(_split_space_list(wait_pids), terminate_process_func=terminate_process_func)
    warnings: list[str] = []
    for relative_path in _split_space_list(update_files):
        source_path = os.path.normpath(os.path.join(temp_path, relative_path))
        target_path = os.path.normpath(os.path.join(cwd_path, relative_path))
        if not os.path.exists(source_path):
            warnings.append(source_path)
            continue
        try:
            if os.path.exists(target_path) and os.path.samefile(source_path, target_path):
                continue
        except OSError:
            pass
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except PermissionError:
                warnings.append(target_path)
                continue
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        os.rename(source_path, target_path)
    if new_tool and os.path.exists(new_tool):
        launch_path = os.path.normpath(os.path.join(cwd_path, build_tool_binary_name(os_name=os_name)))
        shutil.copyfile(new_tool, launch_path)
        current_pid = os.getpid() if current_pid is None else current_pid
        return UpdateApplyResult(
            success=True,
            launch_path=launch_path,
            settings_updates={'wait_pids': str(current_pid), 'update_done': 'true'},
            warning_paths=tuple(warnings),
        )
    return UpdateApplyResult(
        success=False,
        settings_updates={'version': version_old or '', 'updating': 'false'},
        warning_paths=tuple(warnings),
    )


def cleanup_completed_update(
    *,
    updater_path: str,
    new_tool: str | None,
    wait_pids: str | None,
    terminate_process_func: Callable[[int], object] = _terminate_process,
) -> UpdateCleanupResult:
    """Best-effort cleanup after the relaunched tool reports update completion."""
    _terminate_pids(_split_space_list(wait_pids), terminate_process_func=terminate_process_func)
    remove_paths = [updater_path]
    if new_tool:
        remove_paths.append(new_tool)
    removed: list[str] = []
    failed: list[str] = []
    for path in remove_paths:
        if not path or not os.path.exists(path):
            continue
        try:
            os.remove(path)
            removed.append(path)
        except OSError:
            failed.append(path)
    return UpdateCleanupResult(removed_paths=tuple(removed), failed_paths=tuple(failed))
