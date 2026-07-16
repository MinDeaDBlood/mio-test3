from __future__ import annotations

from typing import cast

from src.app.runtime.contexts.contracts import (
    HostWindowProtocol,
    MessagePopProtocol,
    SchedulerHostProtocol,
    UiSchedulerProtocol,
    VariableProtocol,
)


def resolve_ui_host_window(
    host_window: SchedulerHostProtocol | None = None,
) -> SchedulerHostProtocol:
    if host_window is not None:
        return host_window
    from src.app.runtime.window_access import require_main_window

    return cast(SchedulerHostProtocol, require_main_window())


def resolve_ui_host_window_optional(
    host_window: SchedulerHostProtocol | None = None,
) -> SchedulerHostProtocol | None:
    if host_window is not None:
        return host_window
    from src.app.runtime.window_access import get_main_window

    value = get_main_window()
    return cast(SchedulerHostProtocol, value) if value is not None else None


def resolve_default_message_pop(
    message_pop: MessagePopProtocol | None = None,
    *,
    host_window: HostWindowProtocol | None = None,
) -> MessagePopProtocol | None:
    if message_pop is not None:
        return message_pop
    resolved_window = cast(
        HostWindowProtocol,
        resolve_ui_host_window(host_window),
    )
    return resolved_window.message_pop


def resolve_ui_scheduler(
    host_window: SchedulerHostProtocol | None = None,
) -> UiSchedulerProtocol:
    from src.app.ui_scheduler import resolve_app_ui_scheduler

    return resolve_app_ui_scheduler(host_window)


def resolve_language(
    language_var: VariableProtocol | None = None,
) -> VariableProtocol:
    if language_var is not None:
        return language_var
    from src.app.runtime.window_access import require_language

    return cast(VariableProtocol, require_language())


def resolve_theme(
    theme_var: VariableProtocol | None = None,
) -> VariableProtocol:
    if theme_var is not None:
        return theme_var
    from src.app.runtime.window_access import require_theme

    return cast(VariableProtocol, require_theme())


def resolve_language_optional(
    language_var: VariableProtocol | None = None,
) -> VariableProtocol | None:
    if language_var is not None:
        return language_var
    from src.app.runtime.window_access import get_language

    value = get_language()
    return cast(VariableProtocol, value) if value is not None else None


__all__ = [
    'resolve_default_message_pop',
    'resolve_language',
    'resolve_language_optional',
    'resolve_theme',
    'resolve_ui_host_window',
    'resolve_ui_host_window_optional',
    'resolve_ui_scheduler',
]
