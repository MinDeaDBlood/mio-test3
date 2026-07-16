from __future__ import annotations

from src.ui.localization import LocalizationCatalog
from src.ui.warn.dialogs import ask_win


_UNSAVED_OPERATION_MESSAGE = "common_restart_confirmation_unsaved_operation_message"


def confirm_restart_with_active_tasks(*, texts: LocalizationCatalog) -> bool:
    return bool(
        ask_win(
            texts.resolve_required_ui_text(_UNSAVED_OPERATION_MESSAGE),
            texts=texts,
            is_top=True,
        )
    )


__all__ = ["confirm_restart_with_active_tasks"]
