from __future__ import annotations

import os
import shutil

from src.core.random_utils import v_code
from src.logic.common.messages import message
from src.logic.projects.import_flow.models import ProjectImportResult


def _source_folder_name(dir_path: str) -> str:
    return os.path.basename(os.path.normpath(dir_path))


def _unique_project_name(name: str, *, runtime) -> str:
    return name + v_code() if runtime.project_manager.exist(name) else name


def _is_same_workspace_folder(dir_path: str, name: str, *, runtime) -> bool:
    target_path = runtime.project_manager.get_work_path(name)
    return os.path.exists(target_path) and os.path.samefile(
        target_path, os.path.abspath(dir_path)
    )


def import_project_folder(dir_path: str, *, runtime) -> ProjectImportResult:
    name = _source_folder_name(dir_path)
    runtime.output.log(message("copying_project", "Copying project: {name}", name=name))
    if not os.path.exists(dir_path):
        return ProjectImportResult.failure("Project folder does not exist.")
    if _is_same_workspace_folder(dir_path, name, runtime=runtime):
        return ProjectImportResult.failure(
            "Source folder is already the selected project."
        )
    name = _unique_project_name(name, runtime=runtime)
    project_path = runtime.project_manager.new(name)
    shutil.copytree(dir_path, project_path, dirs_exist_ok=True)
    return ProjectImportResult.success(project_name=name)


__all__ = ["import_project_folder"]
