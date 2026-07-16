from __future__ import annotations

LEGACY_WINDOWS_WARNING_MESSAGE = "startup_status_legacy_windows_warning_message"
LEGACY_WINDOWS_CONFIRM_BUTTON = "startup_status_legacy_windows_confirm_button"
LEGACY_WINDOWS_CANCEL_BUTTON = "startup_status_legacy_windows_cancel_button"

STARTUP_STATUS_HOME_WELCOME_MESSAGE = 'startup_status_home_welcome_message'
STARTUP_STATUS_STARTUP_DURATION_FORMAT = 'startup_status_startup_duration_format'

__all__ = [name for name in globals() if name.isupper()]
