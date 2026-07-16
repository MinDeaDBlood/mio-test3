from __future__ import annotations

from src.app.runtime.contexts.contracts import VariableProtocol
from src.app.runtime.contexts.project_defaults import CommonProjectDefaults
from src.app.runtime.contexts.settings import resolve_settings



def resolve_project_manager(project_manager=None):
    if project_manager is not None:
        return project_manager
    from src.app.runtime.core_access import require_project_manager
    return require_project_manager()



def resolve_current_project_name(
    current_project_name: VariableProtocol | None = None,
) -> VariableProtocol:
    value = current_project_name
    if value is None:
        from src.app.runtime.window_access import require_current_project_name

        value = require_current_project_name()
    if not isinstance(value, VariableProtocol):
        raise TypeError("Current project name must provide get() and set().")
    return value



def resolve_context_rule_file(context_rule_file=None):
    if context_rule_file is not None:
        return str(context_rule_file)
    from src.app.runtime.defaults_access import require_context_rule_file
    return str(require_context_rule_file())



def resolve_common_project_defaults(*, settings=None, project_manager=None, current_project_name=None) -> CommonProjectDefaults:
    return CommonProjectDefaults(
        settings=resolve_settings(settings),
        project_manager=resolve_project_manager(project_manager),
        current_project_name=resolve_current_project_name(current_project_name),
    )


__all__ = [
    'resolve_common_project_defaults',
    'resolve_context_rule_file',
    'resolve_current_project_name',
    'resolve_project_manager',
]
