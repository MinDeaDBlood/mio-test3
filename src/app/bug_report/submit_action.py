from __future__ import annotations

import os

from src.app.background_jobs import start_background_job
from src.app.bug_report.controller import BugReportController
from src.app.bug_report_runtime import build_bug_report_runtime_context
from src.app.composition.dialogs import choose_directory as choose_directory_dialog
from src.app.localization_runtime import lang
from src.app.bug_report import submit_action_keys as keys
from src.core.paths import prog_path


def submit(namespace: dict | None = None):
    del namespace
    controller = BugReportController(
        context=build_bug_report_runtime_context(),
        choose_output=(
            lambda: choose_directory_dialog(
                title=lang.resolve_required_ui_text(keys.OUTPUT_DIRECTORY_DIALOG_TITLE)
            )
            if os.name == "nt"
            else prog_path
        ),
        start_worker=start_background_job,
    )
    return controller.request_generation()


__all__ = ["submit"]
