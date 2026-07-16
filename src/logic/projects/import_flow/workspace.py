from __future__ import annotations

from dataclasses import dataclass
from src.logic.projects.common.runtime_context import ProjectWorkspacePort
from src.logic.projects.unpack.runtime_context import UnpackWorkflowRuntimeContext


@dataclass(frozen=True)
class ImportWorkspacePaths:
    project_name: str
    root_path: str
    input_path: str
    unpack_path: str
    output_path: str


def ensure_import_workspace(
    project_manager: ProjectWorkspacePort, project_name: str
) -> ImportWorkspacePaths:
    root_path = project_manager.new(project_name)
    return ImportWorkspacePaths(
        project_name=project_name,
        root_path=str(root_path),
        input_path=str(project_manager.get_input_path(project_name)),
        unpack_path=str(project_manager.get_unpack_path(project_name)),
        output_path=str(project_manager.get_output_path(project_name)),
    )


def build_import_unpack_runtime(
    runtime, paths: ImportWorkspacePaths
) -> UnpackWorkflowRuntimeContext:
    return UnpackWorkflowRuntimeContext(
        input_path=paths.input_path,
        work_path=paths.unpack_path,
        output_path=paths.output_path,
        project_selected=True,
        tool_bin=runtime.tool_bin,
        magisk_not_decompress=runtime.magisk_not_decompress,
        boot_skip_ramdisk=runtime.boot_skip_ramdisk,
        output=runtime.output,
    )


__all__ = [
    "ImportWorkspacePaths",
    "ProjectWorkspacePort",
    "build_import_unpack_runtime",
    "ensure_import_workspace",
]
