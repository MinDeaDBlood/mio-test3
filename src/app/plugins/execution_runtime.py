from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from src.app.runtime.contexts.plugins import resolve_plugin_execute_defaults
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.platform.runtime_paths import PLUGIN_RUNTIME_DIR


@dataclass(frozen=True, slots=True)
class PluginExecutionRuntime:
    project_name: str
    project_work_path: str
    project_output_path: str
    tool_bin: str
    tool_version: str
    language: str
    temp_path: str
    module_exec: str
    output: ServiceOutput
    values: Mapping[str, object]


def build_plugin_execution_runtime(
    *,
    values: Mapping[str, object],
    output: ServiceOutput | None = None,
) -> PluginExecutionRuntime:
    defaults = resolve_plugin_execute_defaults(temp_path=str(PLUGIN_RUNTIME_DIR))
    return PluginExecutionRuntime(
        project_name=str(defaults.current_project_name.get()),
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


__all__ = ["PluginExecutionRuntime", "build_plugin_execution_runtime"]
