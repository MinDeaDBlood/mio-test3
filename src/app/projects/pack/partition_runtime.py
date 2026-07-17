from __future__ import annotations

from dataclasses import dataclass

from src.app.runtime.contexts.projects import (
    resolve_context_rule_file,
    resolve_project_manager,
)
from src.app.runtime.contexts.plugins import resolve_plugin_lifecycle
from src.app.runtime.contexts.settings import resolve_settings
from src.app.runtime.contexts.ui import resolve_ui_host_window
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.projects.pack.runtime_context import PackPartitionRuntimeContext
from src.platform.plugin_lifecycle import PluginLifecycleAdapter


@dataclass(frozen=True)
class PackPartitionApplicationRuntime:
    workflow: PackPartitionRuntimeContext
    plugin_lifecycle: PluginLifecycleAdapter


def build_pack_partition_runtime(
    *, output: ServiceOutput | None = None
) -> PackPartitionApplicationRuntime:
    project_manager = resolve_project_manager()
    settings = resolve_settings()
    workflow = PackPartitionRuntimeContext(
        input_path=project_manager.current_input_path(),
        work_path=project_manager.current_work_path(),
        output_path=project_manager.current_work_output_path(),
        project_selected=project_manager.exist(),
        context_patch_enabled=str(settings.contextpatch) == "1",
        context_rule_file=resolve_context_rule_file(),
        tool_bin=str(settings.tool_bin),
        magisk_not_decompress=str(settings.magisk_not_decompress),
        boot_skip_ramdisk=str(settings.boot_skip_ramdisk),
        output=output or build_service_output(),
    )
    return PackPartitionApplicationRuntime(
        workflow=workflow,
        plugin_lifecycle=resolve_plugin_lifecycle(),
    )


def resolve_pack_partition_host_window():
    return resolve_ui_host_window()


__all__ = [
    "PackPartitionApplicationRuntime",
    "build_pack_partition_runtime",
    "resolve_pack_partition_host_window",
]
