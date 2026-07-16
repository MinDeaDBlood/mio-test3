"""Synchronization for the four typed runtime phases."""

from __future__ import annotations

from src.app.runtime.errors import UnknownRuntimeKeyError
from src.app.runtime.phases import (
    register_core_runtime_services,
    sync_registered_bootstrap_ui_runtime,
    sync_registered_bootstrap_window_runtime,
    sync_registered_core_runtime_services,
    sync_registered_early_runtime_defaults,
)


def _bind_project_selection_after_sync(values: dict[str, object]) -> None:
    from src.app.runtime.phases import (
        get_registered_bootstrap_window_runtime,
        get_registered_core_runtime_services,
    )

    services = get_registered_core_runtime_services()
    if services is None:
        return
    selected = values.get('current_project_name')
    if selected is None and 'project_manager' in values:
        window_runtime = get_registered_bootstrap_window_runtime()
        selected = None if window_runtime is None else window_runtime.current_project_name
    if selected is not None:
        services.project_manager.bind_current_project_name(selected)


def sync_runtime_globals(**kwargs):
    remaining = dict(kwargs)
    for sync_fn in (
        sync_registered_early_runtime_defaults,
        sync_registered_core_runtime_services,
        sync_registered_bootstrap_window_runtime,
        sync_registered_bootstrap_ui_runtime,
    ):
        applied = sync_fn(**remaining)
        for original_name in tuple(remaining):
            if original_name in applied:
                remaining.pop(original_name)
    if remaining:
        names = ', '.join(sorted(remaining))
        raise UnknownRuntimeKeyError(f'Unknown runtime values: {names}')
    _bind_project_selection_after_sync(kwargs)
    return kwargs


def sync_core_runtime_services(**kwargs):
    return register_core_runtime_services(**kwargs)


__all__ = ['sync_core_runtime_services', 'sync_runtime_globals']
