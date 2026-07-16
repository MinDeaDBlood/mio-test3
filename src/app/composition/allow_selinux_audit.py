from __future__ import annotations

import logging

from src.app.composition._ui_task import build_window_task_runtime
from src.app.composition.dialogs import choose_directory, choose_file
from src.app.localization_runtime import lang
from src.app.tools.allow_selinux_audit_controller import SelinuxAuditAllowController
from src.ui.tabs.tools.allow_selinux_audit import keys
from src.ui.tabs.tools.allow_selinux_audit.window import SelinuxAuditAllow


def open_allow_selinux_audit_window() -> SelinuxAuditAllow:
    text = lang.resolve_required_ui_text
    window = SelinuxAuditAllow(
        language=lang,
        choose_log_file=lambda: choose_file(
            title=text(keys.LOG_FILE_DIALOG_TITLE),
            filetypes=(
                (text(keys.LOG_FILE_DIALOG_LOG_FILES), "*.log"),
                (text(keys.LOG_FILE_DIALOG_TEXT_FILES), "*.txt"),
            ),
        ),
        choose_output_directory=lambda: choose_directory(
            title=text(keys.OUTPUT_DIRECTORY_DIALOG_TITLE)
        ),
    )
    _, task_runner = build_window_task_runtime(window, logger=logging)
    window.attach(controller=SelinuxAuditAllowController(task_runner=task_runner))
    return window


__all__ = ["open_allow_selinux_audit_window"]
