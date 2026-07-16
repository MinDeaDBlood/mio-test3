from __future__ import annotations

from dataclasses import dataclass

from src.app.runtime.contexts.contracts import (
    ModuleErrorCodesProtocol,
    ModuleManagerProtocol,
    ProjectManagerProtocol,
    SettingsProtocol,
    VariableProtocol,
)
from src.app.runtime.contexts.paths import resolve_temp_path
from src.app.runtime.contexts.project_defaults import CommonProjectDefaults
from src.app.runtime.contexts.projects import resolve_common_project_defaults


@dataclass(frozen=True)
class PluginExecuteDefaults:
    settings: SettingsProtocol
    current_project_name: VariableProtocol
    project_manager: ProjectManagerProtocol
    temp_path: str
    module_exec: str



def resolve_module_exec(module_exec: str | None = None) -> str:
    if module_exec is not None:
        return str(module_exec)
    from src.app.runtime.defaults_access import get_module_exec
    from src.app.runtime.phases import get_registered_early_runtime_defaults

    bundle = get_registered_early_runtime_defaults()
    if bundle is not None and bundle.module_exec:
        return str(bundle.module_exec)
    return str(get_module_exec())



def resolve_module_manager(module_manager: ModuleManagerProtocol | None = None):
    if module_manager is not None:
        return module_manager
    from src.app.runtime.core_access import require_module_manager
    from src.app.runtime.phases import get_registered_core_runtime_services

    bundle = get_registered_core_runtime_services()
    if bundle is not None:
        return bundle.module_manager
    return require_module_manager()



def resolve_module_error_codes(module_error_codes: ModuleErrorCodesProtocol | None = None):
    if module_error_codes is not None:
        return module_error_codes
    from src.app.runtime.core_access import require_module_error_codes
    from src.app.runtime.phases import get_registered_core_runtime_services

    bundle = get_registered_core_runtime_services()
    if bundle is not None:
        return bundle.module_error_codes
    return require_module_error_codes()



def resolve_plugin_execute_defaults(*, settings=None, current_project_name=None, project_manager=None, temp_path=None, module_exec=None) -> PluginExecuteDefaults:
    common: CommonProjectDefaults = resolve_common_project_defaults(
        settings=settings,
        project_manager=project_manager,
        current_project_name=current_project_name,
    )
    return PluginExecuteDefaults(
        settings=common.settings,
        current_project_name=common.current_project_name,
        project_manager=common.project_manager,
        temp_path=resolve_temp_path(temp_path),
        module_exec=resolve_module_exec(module_exec),
    )


__all__ = [
    'PluginExecuteDefaults',
    'resolve_module_error_codes',
    'resolve_module_exec',
    'resolve_module_manager',
    'resolve_plugin_execute_defaults',
]
