from __future__ import annotations

from collections.abc import Callable

from src.ui.localization import LocalizationCatalog
from src.ui.warn.dialogs import ask_win
from src.ui import startup_status_keys as keys


def present_basic_mode_notice(
    *, texts: LocalizationCatalog, emit: Callable[[str], object]
) -> None:
    emit(texts.resolve_required_ui_text(keys.STARTUP_STATUS_HOME_WELCOME_MESSAGE))


def present_startup_duration(
    seconds: float, *, texts: LocalizationCatalog, emit: Callable[[str], object]
) -> None:
    emit(texts.resolve_required_ui_text(keys.STARTUP_STATUS_STARTUP_DURATION_FORMAT) % seconds)


def present_legacy_windows_warning(*, texts: LocalizationCatalog) -> None:
    ask_win(
        texts.resolve_required_ui_text(keys.LEGACY_WINDOWS_WARNING_MESSAGE),
        texts=texts,
        ok=texts.resolve_required_ui_text(keys.LEGACY_WINDOWS_CONFIRM_BUTTON),
        cancel=texts.resolve_required_ui_text(keys.LEGACY_WINDOWS_CANCEL_BUTTON),
    )


__all__ = [
    "present_basic_mode_notice",
    "present_legacy_windows_warning",
    "present_startup_duration",
]
