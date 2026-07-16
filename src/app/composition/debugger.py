from __future__ import annotations

import logging
import os

from src.app.background_jobs import start_background_job
from src.app.bug_report_runtime import build_bug_report_runtime_context
from src.app.composition.dialogs import choose_directory
from src.app.localization_runtime import lang
from src.app.composition import debugger_keys as keys
from src.app.log_interface.debugger_controller import DebuggerController
from src.app.pro_runtime import is_pro
from src.app.runtime.contexts.settings import resolve_settings, resolve_states
from src.app.runtime.contexts.tooling import resolve_tool_log
from src.platform.system_shell import open_external_url
from src.core.paths import prog_path
from src.app.bug_report.controller import BugReportController
from src.ui.log_interface.debugger import Debugger


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


def open_debugger_window() -> Debugger:
    controller = DebuggerController(
        states=resolve_states(),
        settings_obj=resolve_settings(),
        tool_log=resolve_tool_log(),
        namespace=globals(),
    )
    window = Debugger(
        texts=lang,
        controller=controller,
        generate_bug_report=_bug_report_controller().request_generation,
        open_url=open_external_url,
        show_banner=not is_pro,
    )
    return window


__all__ = ["open_debugger_window"]
