from __future__ import annotations

import os
import shutil
from shutil import copy2
from typing import Callable

from src.core.random_utils import v_code
from src.logic.projects.import_flow.auto_unpack import list_auto_unpack_candidates
from src.logic.projects.import_flow.models import ProjectImportResult
from src.logic.projects.import_flow.workspace import (
    build_import_unpack_runtime,
    ensure_import_workspace,
)


def _build_unique_project_name(project_manager, file_name: str) -> str:
    base_name = os.path.splitext(file_name)[0]
    return base_name + v_code() if project_manager.exist(base_name) else base_name


def _normalize_imported_file(project_dir: str, file_name: str) -> str:
    imported_path = os.path.join(project_dir, file_name)
    if not os.path.exists(imported_path):
        return imported_path
    if "." not in file_name:
        normalized_path = os.path.join(project_dir, file_name + ".img")
        shutil.move(imported_path, normalized_path)
        return normalized_path
    if file_name.endswith(".bin"):
        normalized_path = os.path.join(project_dir, file_name[:-4] + ".img")
        shutil.move(imported_path, normalized_path)
        return normalized_path
    return imported_path


def import_known_file(
    ifile: str,
    *,
    runtime,
    unpack_func: Callable[..., object],
    workflow_runtime: object | None = None,
) -> ProjectImportResult:
    file_name = os.path.basename(ifile)
    project_name = _build_unique_project_name(runtime.project_manager, file_name)
    try:
        paths = ensure_import_workspace(runtime.project_manager, project_name)
    except (OSError, RuntimeError, ValueError) as exc:
        runtime.output.report(str(exc))
        return ProjectImportResult.failure(str(exc))

    copy2(ifile, paths.input_path)
    copy2(ifile, paths.unpack_path)
    _normalize_imported_file(paths.unpack_path, file_name)
    if runtime.auto_unpack:
        unpack_func(
            list_auto_unpack_candidates(paths.unpack_path),
            runtime=workflow_runtime or build_import_unpack_runtime(runtime, paths),
        )
    return ProjectImportResult.success(project_name=project_name)


__all__ = ["import_known_file"]
