"""Typed accessors for core runtime services.

Application code reads only the registered core runtime bundle. The separate
legacy runtime store is not an alternate source for these dependencies.
"""

from __future__ import annotations

from typing import Any

from src.app.runtime.errors import MissingRuntimeValueError
from src.app.runtime.phases import get_registered_core_runtime_services


def get_project_manager() -> Any | None:
    bundle = get_registered_core_runtime_services()
    return None if bundle is None else bundle.project_manager


def require_project_manager() -> Any:
    value = get_project_manager()
    if value is None:
        raise MissingRuntimeValueError(
            "Required core runtime service 'project_manager' is not registered yet"
        )
    return value


def get_module_manager() -> Any | None:
    bundle = get_registered_core_runtime_services()
    return None if bundle is None else bundle.module_manager


def require_module_manager() -> Any:
    value = get_module_manager()
    if value is None:
        raise MissingRuntimeValueError(
            "Required core runtime service 'module_manager' is not registered yet"
        )
    return value


def get_settings() -> Any | None:
    bundle = get_registered_core_runtime_services()
    return None if bundle is None else bundle.settings


def require_settings() -> Any:
    value = get_settings()
    if value is None:
        raise MissingRuntimeValueError(
            "Required core runtime service 'settings' is not registered yet"
        )
    return value


def get_module_error_codes() -> Any | None:
    bundle = get_registered_core_runtime_services()
    return None if bundle is None else bundle.module_error_codes


def require_module_error_codes() -> Any:
    value = get_module_error_codes()
    if value is None:
        raise MissingRuntimeValueError(
            "Required core runtime service 'module_error_codes' is not registered yet"
        )
    return value


__all__ = [
    "get_module_error_codes",
    "get_module_manager",
    "get_project_manager",
    "get_settings",
    "require_module_error_codes",
    "require_module_manager",
    "require_project_manager",
    "require_settings",
]
