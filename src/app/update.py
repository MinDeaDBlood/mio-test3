from __future__ import annotations

import logging

from src.app.composition.update import open_update_window
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.update_runtime import fetch_current_release_check, resolve_update_url
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner
from src.logic.update.models import ReleaseCheckResult


def open_updater(*, auto_start: bool = True):
    try:
        return open_update_window(auto_start=auto_start)
    except RuntimeError:
        logging.debug('Updater window is already active; skipping duplicate open request.')
        return None


def check_upgrade() -> bool:
    try:
        result = fetch_current_release_check(resolve_update_url())
    except (OSError, RuntimeError, TypeError, ValueError):
        return False
    if result.has_update and result.new_version:
        open_updater()
        return True
    return False


def check_upgrade_async(host_window=None) -> None:
    host_window = host_window or resolve_ui_host_window()
    dispatcher = build_ui_dispatcher(host_window=host_window)
    task_runner = build_ui_task_runner(
        dispatcher=dispatcher,
        is_alive=host_window.winfo_exists,
        logger=logging,
    )

    def handle_result(result: ReleaseCheckResult) -> None:
        if result.has_update and result.new_version:
            open_updater()

    task_runner.run(fetch_current_release_check, resolve_update_url(), on_success=handle_result)


__all__ = ['check_upgrade', 'check_upgrade_async', 'open_updater']
