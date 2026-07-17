from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class PluginEntryKind(str, Enum):
    PYTHON = "python"
    SHELL = "shell"
    VIRTUAL = "virtual"


@dataclass(frozen=True, slots=True)
class PluginExecutionPlan:
    plugin_id: str
    plugin_name: str
    entry_kind: PluginEntryKind | None
    entry_path: str
    error_code: str
    error_default: str
    error_params: Mapping[str, object]

    @property
    def can_execute(self) -> bool:
        return self.entry_kind is not None and not self.error_code


def _error(
    plugin_id: str,
    plugin_name: str,
    code: str,
    default: str,
    **params: object,
) -> PluginExecutionPlan:
    return PluginExecutionPlan(
        plugin_id=plugin_id,
        plugin_name=plugin_name,
        entry_kind=None,
        entry_path="",
        error_code=code,
        error_default=default,
        error_params=params,
    )


def plan_plugin_execution(
    plugin_id: str,
    *,
    project_name: str,
    inspection: Mapping[str, object],
) -> PluginExecutionPlan:
    """Apply plugin execution rules without touching files or processes."""
    normalized_id = str(plugin_id).strip()
    plugin_name = str(inspection.get("plugin_name") or normalized_id)
    if not normalized_id:
        return _error(
            normalized_id,
            plugin_name,
            "plugin_id_missing",
            "Plugin identifier is missing.",
        )
    if not str(project_name).strip():
        return _error(
            normalized_id,
            plugin_name,
            "project_not_selected",
            "Project is not selected",
        )

    virtual = bool(inspection.get("virtual"))
    if virtual:
        return PluginExecutionPlan(
            plugin_id=normalized_id,
            plugin_name=plugin_name,
            entry_kind=PluginEntryKind.VIRTUAL,
            entry_path="",
            error_code="",
            error_default="",
            error_params={},
        )

    if not bool(inspection.get("plugin_exists")):
        return _error(
            normalized_id,
            plugin_name,
            "plugin_not_found",
            "Plugin not found: {plugin_id}",
            plugin_id=normalized_id,
        )

    manifest_state = str(inspection.get("manifest_state") or "missing")
    if manifest_state == "missing":
        return _error(
            normalized_id,
            plugin_name,
            "plugin_manifest_missing",
            "Plugin {plugin} configuration is missing.",
            plugin=plugin_name,
        )
    if manifest_state == "invalid":
        return _error(
            normalized_id,
            plugin_name,
            "plugin_manifest_invalid",
            "Plugin {plugin} configuration is corrupted.",
            plugin=plugin_name,
        )
    if manifest_state == "unreadable":
        return _error(
            normalized_id,
            plugin_name,
            "plugin_manifest_unreadable",
            "Error accessing plugin {plugin} configuration.",
            plugin=plugin_name,
        )

    missing_dependencies = tuple(
        str(value) for value in inspection.get("missing_dependencies") or () if value
    )
    if missing_dependencies:
        dependency = missing_dependencies[0]
        return _error(
            normalized_id,
            plugin_name,
            "plugin_dependency_missing",
            "Plugin {plugin} requires missing dependency {dependency}",
            plugin=plugin_name,
            dependency=dependency,
        )

    shell_path = str(inspection.get("shell_entry_path") or "")
    python_path = str(inspection.get("python_entry_path") or "")
    if shell_path:
        return PluginExecutionPlan(
            plugin_id=normalized_id,
            plugin_name=plugin_name,
            entry_kind=PluginEntryKind.SHELL,
            entry_path=shell_path,
            error_code="",
            error_default="",
            error_params={},
        )
    if python_path:
        return PluginExecutionPlan(
            plugin_id=normalized_id,
            plugin_name=plugin_name,
            entry_kind=PluginEntryKind.PYTHON,
            entry_path=python_path,
            error_code="",
            error_default="",
            error_params={},
        )

    return _error(
        normalized_id,
        plugin_name,
        "plugin_entry_missing",
        "Plugin entry point is missing: {plugin}",
        plugin=plugin_name,
    )


__all__ = [
    "PluginEntryKind",
    "PluginExecutionPlan",
    "plan_plugin_execution",
]
