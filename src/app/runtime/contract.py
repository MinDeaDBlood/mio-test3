"""Runtime phase contracts and fail-fast validation."""

from __future__ import annotations

from typing import Iterable

from src.app.runtime.errors import MissingRuntimeValueError
from src.app.runtime.phases import export_registered_runtime_values

EARLY_RUNTIME_DEFAULT_KEYS = frozenset({'call', 'context_rule_file', 'module_exec', 'states', 'temp', 'log_dir', 'tool_log', 'tool_self', 'prog_path'})
CORE_RUNTIME_KEYS = frozenset({*EARLY_RUNTIME_DEFAULT_KEYS, 'module_error_codes', 'module_manager', 'project_manager', 'settings'})
BOOTSTRAP_WINDOW_KEYS = frozenset({'animation', 'current_project_name', 'language', 'theme', 'main_window', 'ui_scheduler'})
BOOTSTRAP_UI_KEYS = frozenset({*CORE_RUNTIME_KEYS, *BOOTSTRAP_WINDOW_KEYS, 'project_menu', 'unpack_view'})


def missing_runtime_keys(required_keys: Iterable[str], runtime_values: dict[str, object] | None = None) -> list[str]:
    values = export_registered_runtime_values() if runtime_values is None else dict(runtime_values)
    return sorted(key for key in required_keys if values.get(key) is None)


def validate_runtime_keys(required_keys: Iterable[str], *, runtime_values: dict[str, object] | None = None, context: str = 'runtime') -> dict[str, object]:
    values = export_registered_runtime_values() if runtime_values is None else dict(runtime_values)
    missing = missing_runtime_keys(required_keys, values)
    if missing:
        raise MissingRuntimeValueError(f"{context} is missing required runtime keys: {', '.join(missing)}")
    return values


__all__ = ['BOOTSTRAP_UI_KEYS', 'BOOTSTRAP_WINDOW_KEYS', 'CORE_RUNTIME_KEYS', 'EARLY_RUNTIME_DEFAULT_KEYS', 'missing_runtime_keys', 'validate_runtime_keys']
