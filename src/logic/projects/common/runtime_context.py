from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.logic.common.service_output import ServiceOutput, build_service_output


class ProjectNamePort(Protocol):
    def get(self) -> object: ...
    def set(self, value: object) -> object: ...


class ProjectPathRuntime(Protocol):
    workspace_path: str
    current_project_name: ProjectNamePort | None


class ProjectWorkspacePort(Protocol):
    def exist(self, name: str | None = None) -> bool: ...
    def new(self, name: str) -> str: ...
    def remove(self, name: str) -> bool: ...
    def get_work_path(self, name: str) -> str: ...
    def get_input_path(self, name: str) -> str: ...
    def get_unpack_path(self, name: str) -> str: ...
    def get_output_path(self, name: str) -> str: ...


@dataclass(frozen=True)
class ProjectPathRuntimeContext:
    workspace_path: str
    current_project_name: ProjectNamePort | None = None


@dataclass(frozen=True)
class ProjectImportRuntimeContext:
    project_manager: ProjectWorkspacePort
    auto_unpack: bool
    tool_bin: str
    magisk_not_decompress: str
    boot_skip_ramdisk: str
    output: ServiceOutput
    ofp_mtk_decrypt: bool | None = None


def build_project_path_runtime_context(
    *,
    workspace_path: str,
    current_project_name: ProjectNamePort | None = None,
) -> ProjectPathRuntimeContext:
    if not str(workspace_path).strip():
        raise ValueError("Project path runtime requires workspace_path.")
    return ProjectPathRuntimeContext(
        workspace_path=str(workspace_path),
        current_project_name=current_project_name,
    )


def resolve_project_workspace_path(runtime: ProjectPathRuntime) -> str:
    path = str(runtime.workspace_path or "").strip()
    if not path:
        raise RuntimeError("Project path runtime has no workspace_path.")
    return path


def resolve_project_path_current_project_name(
    runtime: ProjectPathRuntime,
) -> ProjectNamePort:
    if runtime.current_project_name is None:
        raise RuntimeError("Project path runtime has no current_project_name.")
    return runtime.current_project_name


def build_project_import_runtime_context(
    *,
    project_manager,
    auto_unpack: bool,
    tool_bin: str,
    magisk_not_decompress: str,
    boot_skip_ramdisk: str,
    output: ServiceOutput | None = None,
    ofp_mtk_decrypt: bool | None = None,
) -> ProjectImportRuntimeContext:
    if project_manager is None:
        raise ValueError("Project import runtime requires project_manager.")
    return ProjectImportRuntimeContext(
        project_manager=project_manager,
        auto_unpack=bool(auto_unpack),
        tool_bin=str(tool_bin),
        magisk_not_decompress=str(magisk_not_decompress),
        boot_skip_ramdisk=str(boot_skip_ramdisk),
        output=output or build_service_output(),
        ofp_mtk_decrypt=ofp_mtk_decrypt,
    )


__all__ = [
    "ProjectImportRuntimeContext",
    "ProjectNamePort",
    "ProjectPathRuntime",
    "ProjectPathRuntimeContext",
    "ProjectWorkspacePort",
    "build_project_import_runtime_context",
    "build_project_path_runtime_context",
    "resolve_project_path_current_project_name",
    "resolve_project_workspace_path",
]
