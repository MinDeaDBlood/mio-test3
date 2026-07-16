from __future__ import annotations

import logging
import os

from src.app.background_jobs import start_background_job
from src.app.bug_report_runtime import build_bug_report_runtime_context
from src.app.composition.log_stream import create_stdout_redirector
from src.app.composition.dialogs import choose_directory
from src.app.lifecycle import restart_app
from src.app.localization_runtime import lang
from src.app.composition import crash_keys as keys
from src.app.runtime.contexts.settings import resolve_settings
from src.app.runtime.contexts.tooling import resolve_tool_log
from src.platform.system_shell import open_external_url
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.app.std_streams import ensure_process_streams_installed
from src.core.paths import prog_path
from src.app.bug_report.controller import BugReportController
from src.ui.warn.crash import CrashWindowActions, build_crash_window
from src.ui.warn.models import CrashContext


def _bug_report_controller() -> BugReportController:
    return BugReportController(
        context=build_bug_report_runtime_context(),
        choose_output=lambda: choose_directory(
            title=lang.resolve_required_ui_text(
                keys.BUG_REPORT_OUTPUT_DIRECTORY_DIALOG_TITLE
            )
        )
        if os.name == "nt"
        else prog_path,
        start_worker=start_background_job,
        logger=logging,
    )


def show_crash(code: int, description: str | None = None) -> None:
    settings = resolve_settings()
    root_window = resolve_ui_host_window()
    if settings.debug_mode == "No":
        root_window.withdraw()

    ensure_process_streams_installed()
    report_controller = _bug_report_controller()

    def exit_application() -> None:
        root_window.destroy()

    actions = CrashWindowActions(
        generate_bug_report=report_controller.request_generation,
        restart=lambda window: restart_app(window, confirm_unsaved=lambda: True),
        exit_application=exit_application,
        open_issue_tracker=lambda: open_external_url(
            "https://github.com/ColdWindScholar/MIO-KITCHEN-SOURCE/issues"
        ),
        create_stdout_sink=lambda widget: create_stdout_redirector(widget, stdout=True),
        create_stderr_sink=lambda widget: create_stdout_redirector(
            widget, error_mode=True, stderr=True
        ),
    )
    window = build_crash_window(
        CrashContext(
            code=code,
            description=description
            or lang.resolve_required_ui_text(keys.UNKNOWN_ERROR_DESCRIPTION),
        ),
        root_window=root_window,
        version=settings.version,
        tool_log=resolve_tool_log(),
        actions=actions,
        texts=lang,
    )
    window.wait_window()
    raise SystemExit(1)


__all__ = ["show_crash"]
