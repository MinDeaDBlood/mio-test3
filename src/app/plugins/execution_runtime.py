from __future__ import annotations

from collections.abc import Mapping

from src.app.runtime.contexts.plugins import resolve_plugin_execute_defaults
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.plugins.runtime_context import PluginExecuteRuntimeContext
from src.platform.runtime_paths import PLUGIN_RUNTIME_DIR


def build_plugin_execute_runtime_context(
    *,
    values: Mapping[str, object],
    output: ServiceOutput | None = None,
) -> PluginExecuteRuntimeContext:
    defaults = resolve_plugin_execute_defaults(temp_path=str(PLUGIN_RUNTIME_DIR))
    project_name = str(defaults.current_project_name.get())
    return PluginExecuteRuntimeContext(
        project_name=project_name,
        project_work_path=defaults.project_manager.current_work_path(),
        project_output_path=defaults.project_manager.current_work_output_path(),
        tool_bin=str(defaults.settings.tool_bin),
        tool_version=str(defaults.settings.version),
        language=str(defaults.settings.language),
        temp_path=defaults.temp_path,
        module_exec=defaults.module_exec,
        output=output or build_service_output(),
        values=dict(values),
    )


__all__ = ["build_plugin_execute_runtime_context"]
