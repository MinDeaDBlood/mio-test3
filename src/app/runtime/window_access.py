"""Typed accessors for bootstrap window and UI runtime values."""

from __future__ import annotations

from typing import Any

from src.app.runtime.errors import MissingRuntimeValueError
from src.app.runtime.phases import (
    get_registered_bootstrap_ui_runtime,
    get_registered_bootstrap_window_runtime,
)


def get_animation() -> Any | None:
    bundle = get_registered_bootstrap_window_runtime()
    return None if bundle is None else bundle.animation


def require_animation() -> Any:
    value = get_animation()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap window value 'animation' is not registered yet"
        )
    return value


def get_main_window() -> Any | None:
    bundle = get_registered_bootstrap_window_runtime()
    return None if bundle is None else bundle.main_window


def require_main_window() -> Any:
    value = get_main_window()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap window value 'main_window' is not registered yet"
        )
    return value


def get_win() -> Any | None:
    return get_main_window()


def require_win() -> Any:
    return require_main_window()


def get_current_project_name() -> Any | None:
    bundle = get_registered_bootstrap_window_runtime()
    return None if bundle is None else bundle.current_project_name


def require_current_project_name() -> Any:
    value = get_current_project_name()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap window value 'current_project_name' is not registered yet"
        )
    return value


def get_project_menu() -> Any | None:
    bundle = get_registered_bootstrap_ui_runtime()
    return None if bundle is None else bundle.project_menu


def require_project_menu() -> Any:
    value = get_project_menu()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap UI value 'project_menu' is not registered yet"
        )
    return value


def get_unpack_view() -> Any | None:
    bundle = get_registered_bootstrap_ui_runtime()
    return None if bundle is None else bundle.unpack_view


def require_unpack_view() -> Any:
    value = get_unpack_view()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap UI value 'unpack_view' is not registered yet"
        )
    return value


def get_unpackg() -> Any | None:
    return get_unpack_view()


def require_unpackg() -> Any:
    return require_unpack_view()


def get_language() -> Any | None:
    bundle = get_registered_bootstrap_window_runtime()
    return None if bundle is None else bundle.language


def require_language() -> Any:
    value = get_language()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap window value 'language' is not registered yet"
        )
    return value


def get_theme() -> Any | None:
    bundle = get_registered_bootstrap_window_runtime()
    return None if bundle is None else bundle.theme


def require_theme() -> Any:
    value = get_theme()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap window value 'theme' is not registered yet"
        )
    return value


def get_ui_scheduler() -> Any | None:
    bundle = get_registered_bootstrap_window_runtime()
    return None if bundle is None else bundle.ui_scheduler


def require_ui_scheduler() -> Any:
    value = get_ui_scheduler()
    if value is None:
        raise MissingRuntimeValueError(
            "Required bootstrap window value 'ui_scheduler' is not registered yet"
        )
    return value


__all__ = [
    "get_animation",
    "get_current_project_name",
    "get_language",
    "get_main_window",
    "get_project_menu",
    "get_theme",
    "get_ui_scheduler",
    "get_unpack_view",
    "get_unpackg",
    "get_win",
    "require_animation",
    "require_current_project_name",
    "require_language",
    "require_main_window",
    "require_project_menu",
    "require_theme",
    "require_ui_scheduler",
    "require_unpack_view",
    "require_unpackg",
    "require_win",
]
