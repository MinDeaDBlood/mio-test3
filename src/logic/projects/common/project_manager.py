from __future__ import annotations

import os
from src.logic.projects.common.runtime_context import (
    ProjectPathRuntime,
    build_project_path_runtime_context,
    resolve_project_path_current_project_name,
    resolve_project_workspace_path,
)


PROJECTS_ROOT_DIR_NAME = "Projects"
INPUT_DIR_NAME = "input"
UNPACK_DIR_NAME = "unpack"
OUTPUT_DIR_NAME = "output"


def _clean_project_name(name: str) -> str:
    return str(name or "").replace(" ", "_").strip()


def _normalize_path(path: str) -> str:
    normalized = os.path.abspath(path)
    if os.name == "nt":
        normalized = normalized.replace("\\", "/")
    if not normalized.endswith(("/", os.sep)):
        normalized += os.sep
    return normalized


class ProjectManager:
    def __init__(self, runtime: ProjectPathRuntime):
        if runtime is None:
            raise ValueError(
                "ProjectManager requires an explicit project path runtime."
            )
        # Real projects are isolated under <settings.path>/Projects instead of
        # being mixed with application folders.
        self.hide_items = ["bin", "src", "readmes", PROJECTS_ROOT_DIR_NAME]
        self.runtime = runtime

    def bind_current_project_name(self, current_project_name: object) -> None:
        """Complete the bootstrap runtime after the Tk project variable exists."""
        self.runtime = build_project_path_runtime_context(
            workspace_path=self.workspace_path,
            current_project_name=current_project_name,
        )

    def set_workspace_path(self, workspace_path: str) -> None:
        """Replace the workspace path while preserving the bound project name."""
        self.runtime = build_project_path_runtime_context(
            workspace_path=workspace_path,
            current_project_name=self.runtime.current_project_name,
        )

    @property
    def workspace_path(self) -> str:
        return resolve_project_workspace_path(self.runtime)

    @property
    def current_project_name(self):
        return resolve_project_path_current_project_name(self.runtime)

    def workspace_root_path(self) -> str:
        base = self.workspace_path or os.getcwd()
        os.makedirs(base, exist_ok=True)
        return _normalize_path(base)

    def projects_root_path(self) -> str:
        root = os.path.join(self.workspace_root_path(), PROJECTS_ROOT_DIR_NAME)
        os.makedirs(root, exist_ok=True)
        return _normalize_path(root)

    def get_work_path(self, name):
        clean_name = _clean_project_name(name)
        path = os.path.join(self.projects_root_path(), clean_name)
        return _normalize_path(path)

    def get_projects(self):
        root = self.projects_root_path()
        for entry in sorted(os.scandir(root), key=lambda item: item.name.lower()):
            if entry.is_dir() and not entry.name.startswith("."):
                yield entry.name

    def _ensure_project_root(self, name: str) -> str:
        path = self.get_work_path(name)
        os.makedirs(path, exist_ok=True)
        self._ensure_project_layout(path)
        return path

    def _ensure_project_layout(self, project_root: str) -> None:
        for folder_name in (INPUT_DIR_NAME, UNPACK_DIR_NAME, OUTPUT_DIR_NAME):
            os.makedirs(os.path.join(project_root, folder_name), exist_ok=True)

    def _ensure_subdir_path(self, name: str, folder_name: str) -> str:
        project_root = self._ensure_project_root(name)
        path = os.path.join(project_root, folder_name)
        os.makedirs(path, exist_ok=True)
        return _normalize_path(path)

    def get_input_path(self, name: str) -> str:
        return self._ensure_subdir_path(name, INPUT_DIR_NAME)

    def get_unpack_path(self, name: str) -> str:
        return self._ensure_subdir_path(name, UNPACK_DIR_NAME)

    def get_output_path(self, name: str) -> str:
        return self._ensure_subdir_path(name, OUTPUT_DIR_NAME)

    def new(self, name: str):
        clean_name = _clean_project_name(name)
        return self._ensure_project_root(clean_name)

    def current_project_root_path(self):
        current_name = _clean_project_name(self.current_project_name.get())
        if not current_name:
            return self.projects_root_path()
        return self._ensure_project_root(current_name)

    def current_input_path(self):
        current_name = _clean_project_name(self.current_project_name.get())
        if not current_name:
            return self.projects_root_path()
        return self.get_input_path(current_name)

    def current_unpack_path(self):
        current_name = _clean_project_name(self.current_project_name.get())
        if not current_name:
            return self.projects_root_path()
        return self.get_unpack_path(current_name)

    def current_work_path(self):
        # The active editable workspace is always the unpack folder. Source
        # archives and incoming images may be preserved in input, while rebuilt
        # images are written to output.
        return self.current_unpack_path()

    def current_work_output_path(self):
        current_name = _clean_project_name(self.current_project_name.get())
        if not current_name:
            return self.projects_root_path()
        return self.get_output_path(current_name)

    def exist(self, name=None):
        current_name = _clean_project_name(name or self.current_project_name.get())
        if not current_name:
            return False
        return os.path.exists(self.get_work_path(current_name))

    def remove(self, name):
        from src.logic.projects.common.workspace_service import rmdir

        if not self.exist(name):
            return True
        rmdir(self.get_work_path(name), quiet=True)
        return not self.exist(name)


__all__ = [
    "INPUT_DIR_NAME",
    "OUTPUT_DIR_NAME",
    "PROJECTS_ROOT_DIR_NAME",
    "ProjectManager",
    "UNPACK_DIR_NAME",
]
