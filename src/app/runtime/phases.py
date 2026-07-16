"""Typed runtime phase registration.

This module owns the four explicit startup phase bundles. There is no secondary
key/value store and no alternate lookup path.
"""

from __future__ import annotations

from typing import Any

from src.app.runtime.errors import MissingRuntimeValueError
from src.app.runtime.keys import BOOTSTRAP_UI_KEYS, BOOTSTRAP_WINDOW_KEYS, CORE_RUNTIME_KEYS, EARLY_RUNTIME_KEYS
from src.app.runtime.models import BootstrapUiRuntime, BootstrapWindowRuntime, EarlyRuntimeDefaults, RuntimeBootstrapServices

_REGISTERED_EARLY_RUNTIME_DEFAULTS: EarlyRuntimeDefaults | None = None
_REGISTERED_CORE_RUNTIME_SERVICES: RuntimeBootstrapServices | None = None
_REGISTERED_BOOTSTRAP_WINDOW_RUNTIME: BootstrapWindowRuntime | None = None
_REGISTERED_BOOTSTRAP_UI_RUNTIME: BootstrapUiRuntime | None = None


def _seed(field_names: frozenset[str], bundle: object | None) -> dict[str, Any]:
    if bundle is None:
        return {name: None for name in field_names}
    values = bundle.export_runtime_values()
    return {name: values.get(name) for name in field_names}


def _updated_bundle(*, field_names: frozenset[str], current_bundle: object | None, bundle_factory, updates: dict[str, Any]):
    applied = {name: value for name, value in updates.items() if name in field_names}
    if not applied:
        return {}, current_bundle
    values = _seed(field_names, current_bundle)
    values.update(applied)
    return applied, bundle_factory(**values)


def register_early_runtime_defaults(*, prog_path: str, tool_self: str, temp: str, log_dir: str, tool_log: str, context_rule_file: str, states: Any, call: Any, module_exec: str) -> dict[str, Any]:
    global _REGISTERED_EARLY_RUNTIME_DEFAULTS
    values = dict(
        prog_path=prog_path,
        tool_self=tool_self,
        temp=temp,
        log_dir=log_dir,
        tool_log=tool_log,
        context_rule_file=context_rule_file,
        states=states,
        call=call,
        module_exec=module_exec,
    )
    _REGISTERED_EARLY_RUNTIME_DEFAULTS = EarlyRuntimeDefaults(**values)
    return values


def register_core_runtime_services(*, settings: Any, module_error_codes: Any, module_manager: Any, project_manager: Any) -> dict[str, Any]:
    global _REGISTERED_CORE_RUNTIME_SERVICES
    values = dict(
        settings=settings,
        module_error_codes=module_error_codes,
        module_manager=module_manager,
        project_manager=project_manager,
    )
    _REGISTERED_CORE_RUNTIME_SERVICES = RuntimeBootstrapServices(**values)
    return values


def register_bootstrap_window_runtime(*, main_window: Any, animation: Any, ui_scheduler: Any, current_project_name: Any, theme: Any, language: Any) -> dict[str, Any]:
    global _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME
    values = dict(
        main_window=main_window,
        animation=animation,
        ui_scheduler=ui_scheduler,
        current_project_name=current_project_name,
        theme=theme,
        language=language,
    )
    _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME = BootstrapWindowRuntime(**values)
    return values


def register_bootstrap_ui_runtime(*, unpack_view: Any, project_menu: Any) -> dict[str, Any]:
    global _REGISTERED_BOOTSTRAP_UI_RUNTIME
    values = dict(unpack_view=unpack_view, project_menu=project_menu)
    _REGISTERED_BOOTSTRAP_UI_RUNTIME = BootstrapUiRuntime(**values)
    return values


def sync_registered_early_runtime_defaults(**kwargs: Any) -> dict[str, Any]:
    global _REGISTERED_EARLY_RUNTIME_DEFAULTS
    applied, bundle = _updated_bundle(
        field_names=EARLY_RUNTIME_KEYS,
        current_bundle=_REGISTERED_EARLY_RUNTIME_DEFAULTS,
        bundle_factory=EarlyRuntimeDefaults,
        updates=kwargs,
    )
    if applied:
        _REGISTERED_EARLY_RUNTIME_DEFAULTS = bundle
    return applied


def sync_registered_core_runtime_services(**kwargs: Any) -> dict[str, Any]:
    global _REGISTERED_CORE_RUNTIME_SERVICES
    applied, bundle = _updated_bundle(
        field_names=CORE_RUNTIME_KEYS,
        current_bundle=_REGISTERED_CORE_RUNTIME_SERVICES,
        bundle_factory=RuntimeBootstrapServices,
        updates=kwargs,
    )
    if applied:
        _REGISTERED_CORE_RUNTIME_SERVICES = bundle
    return applied


def sync_registered_bootstrap_window_runtime(**kwargs: Any) -> dict[str, Any]:
    global _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME
    applied, bundle = _updated_bundle(
        field_names=BOOTSTRAP_WINDOW_KEYS,
        current_bundle=_REGISTERED_BOOTSTRAP_WINDOW_RUNTIME,
        bundle_factory=BootstrapWindowRuntime,
        updates=kwargs,
    )
    if applied:
        _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME = bundle
    return applied


def sync_registered_bootstrap_ui_runtime(**kwargs: Any) -> dict[str, Any]:
    global _REGISTERED_BOOTSTRAP_UI_RUNTIME
    applied, bundle = _updated_bundle(
        field_names=BOOTSTRAP_UI_KEYS,
        current_bundle=_REGISTERED_BOOTSTRAP_UI_RUNTIME,
        bundle_factory=BootstrapUiRuntime,
        updates=kwargs,
    )
    if applied:
        _REGISTERED_BOOTSTRAP_UI_RUNTIME = bundle
    return applied


def get_registered_early_runtime_defaults() -> EarlyRuntimeDefaults | None:
    return _REGISTERED_EARLY_RUNTIME_DEFAULTS


def require_registered_early_runtime_defaults() -> EarlyRuntimeDefaults:
    if _REGISTERED_EARLY_RUNTIME_DEFAULTS is None:
        raise MissingRuntimeValueError('Registered early runtime defaults are not available yet')
    return _REGISTERED_EARLY_RUNTIME_DEFAULTS


def get_registered_core_runtime_services() -> RuntimeBootstrapServices | None:
    return _REGISTERED_CORE_RUNTIME_SERVICES


def require_registered_core_runtime_services() -> RuntimeBootstrapServices:
    if _REGISTERED_CORE_RUNTIME_SERVICES is None:
        raise MissingRuntimeValueError('Registered core runtime services are not available yet')
    return _REGISTERED_CORE_RUNTIME_SERVICES


def get_registered_bootstrap_window_runtime() -> BootstrapWindowRuntime | None:
    return _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME


def require_registered_bootstrap_window_runtime() -> BootstrapWindowRuntime:
    if _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME is None:
        raise MissingRuntimeValueError('Registered bootstrap window runtime is not available yet')
    return _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME


def get_registered_bootstrap_ui_runtime() -> BootstrapUiRuntime | None:
    return _REGISTERED_BOOTSTRAP_UI_RUNTIME


def require_registered_bootstrap_ui_runtime() -> BootstrapUiRuntime:
    if _REGISTERED_BOOTSTRAP_UI_RUNTIME is None:
        raise MissingRuntimeValueError('Registered bootstrap UI runtime is not available yet')
    return _REGISTERED_BOOTSTRAP_UI_RUNTIME


def export_registered_runtime_values() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for bundle in (
        _REGISTERED_EARLY_RUNTIME_DEFAULTS,
        _REGISTERED_CORE_RUNTIME_SERVICES,
        _REGISTERED_BOOTSTRAP_WINDOW_RUNTIME,
        _REGISTERED_BOOTSTRAP_UI_RUNTIME,
    ):
        if bundle is not None:
            values.update(bundle.export_runtime_values())
    return values


__all__ = [
    'BootstrapUiRuntime',
    'BootstrapWindowRuntime',
    'export_registered_runtime_values',
    'get_registered_bootstrap_ui_runtime',
    'get_registered_bootstrap_window_runtime',
    'get_registered_core_runtime_services',
    'get_registered_early_runtime_defaults',
    'register_bootstrap_ui_runtime',
    'register_bootstrap_window_runtime',
    'register_core_runtime_services',
    'register_early_runtime_defaults',
    'require_registered_bootstrap_ui_runtime',
    'require_registered_bootstrap_window_runtime',
    'require_registered_core_runtime_services',
    'require_registered_early_runtime_defaults',
    'sync_registered_bootstrap_ui_runtime',
    'sync_registered_bootstrap_window_runtime',
    'sync_registered_core_runtime_services',
    'sync_registered_early_runtime_defaults',
]
