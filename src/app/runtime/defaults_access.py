"""Typed accessors for early runtime defaults.

Application code reads only the registered ``EarlyRuntimeDefaults`` bundle.
The compatibility store is not consulted as an alternate source.
"""

from __future__ import annotations

from typing import Any

from src.app.runtime.errors import MissingRuntimeValueError
from src.app.runtime.phases import get_registered_early_runtime_defaults


def get_temp_path() -> str:
    bundle = get_registered_early_runtime_defaults()
    return "" if bundle is None else str(bundle.temp)


def require_temp_path() -> str:
    bundle = get_registered_early_runtime_defaults()
    if bundle is None:
        raise MissingRuntimeValueError(
            "Required early runtime value 'temp' is not registered yet"
        )
    return str(bundle.temp)


def get_log_dir() -> str:
    bundle = get_registered_early_runtime_defaults()
    return "" if bundle is None else str(bundle.log_dir)


def require_log_dir() -> str:
    bundle = get_registered_early_runtime_defaults()
    if bundle is None:
        raise MissingRuntimeValueError(
            "Required early runtime value 'log_dir' is not registered yet"
        )
    return str(bundle.log_dir)


def get_prog_path() -> str:
    bundle = get_registered_early_runtime_defaults()
    return "" if bundle is None else str(bundle.prog_path)


def require_prog_path() -> str:
    bundle = get_registered_early_runtime_defaults()
    if bundle is None:
        raise MissingRuntimeValueError(
            "Required early runtime value 'prog_path' is not registered yet"
        )
    return str(bundle.prog_path)


def get_tool_self() -> str:
    bundle = get_registered_early_runtime_defaults()
    return "" if bundle is None else str(bundle.tool_self)


def require_tool_self() -> str:
    bundle = get_registered_early_runtime_defaults()
    if bundle is None:
        raise MissingRuntimeValueError(
            "Required early runtime value 'tool_self' is not registered yet"
        )
    return str(bundle.tool_self)


def get_tool_log() -> str:
    bundle = get_registered_early_runtime_defaults()
    return "" if bundle is None else str(bundle.tool_log)


def require_tool_log() -> str:
    bundle = get_registered_early_runtime_defaults()
    if bundle is None:
        raise MissingRuntimeValueError(
            "Required early runtime value 'tool_log' is not registered yet"
        )
    return str(bundle.tool_log)


def get_module_exec() -> str:
    bundle = get_registered_early_runtime_defaults()
    return "" if bundle is None else str(bundle.module_exec)


def get_states() -> Any | None:
    bundle = get_registered_early_runtime_defaults()
    return None if bundle is None else bundle.states


def require_states() -> Any:
    value = get_states()
    if value is None:
        raise MissingRuntimeValueError(
            "Required early runtime value 'states' is not registered yet"
        )
    return value


def get_context_rule_file() -> str:
    bundle = get_registered_early_runtime_defaults()
    return "" if bundle is None else str(bundle.context_rule_file)


def require_context_rule_file() -> Any:
    bundle = get_registered_early_runtime_defaults()
    if bundle is None:
        raise MissingRuntimeValueError(
            "Required early runtime value 'context_rule_file' is not registered yet"
        )
    return bundle.context_rule_file


__all__ = [
    "get_context_rule_file",
    "get_log_dir",
    "get_module_exec",
    "get_prog_path",
    "get_states",
    "get_temp_path",
    "get_tool_log",
    "get_tool_self",
    "require_context_rule_file",
    "require_log_dir",
    "require_prog_path",
    "require_states",
    "require_temp_path",
    "require_tool_log",
    "require_tool_self",
]
