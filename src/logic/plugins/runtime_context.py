from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from src.logic.common.service_output import ServiceOutput


@dataclass(frozen=True)
class PluginExecuteRuntimeContext:
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


__all__ = ["PluginExecuteRuntimeContext"]
