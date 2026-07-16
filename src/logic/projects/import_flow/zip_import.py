from __future__ import annotations

import os
from shutil import copy2
from typing import Callable

from src.logic.common.messages import message
from src.logic.projects.import_flow.archive_handlers import (
    extract_zip_members as default_extract_zip_members,
)
from src.logic.projects.import_flow.auto_unpack import list_auto_unpack_candidates
from src.logic.projects.import_flow.models import ProjectImportResult
from src.logic.projects.import_flow.fs_config_conversion import script2fs as default_script2fs
from src.logic.projects.import_flow.workspace import (
    build_import_unpack_runtime,
    ensure_import_workspace,
)


def _project_name_from_zip(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def import_zip_rom(
    ifile: str,
    *,
    runtime,
    unpack_func: Callable[..., object],
    workflow_runtime: object | None = None,
    script2fs_func: Callable[[str], object] = default_script2fs,
    extract_zip_members_func: Callable[..., object] = default_extract_zip_members,
) -> ProjectImportResult:
    project_name = _project_name_from_zip(ifile)
    paths = ensure_import_workspace(runtime.project_manager, project_name)
    try:
        copy2(ifile, paths.input_path)
    except OSError as exc:
        runtime.output.log(
            message("copy_failed", "Cannot copy {item}: {error}", item=ifile, error=exc)
        )
    extraction_errors: list[str] = []

    def on_zip_member(member_name: str) -> None:
        runtime.output.log(message("processing", "Processing {item}", item=member_name))

    def on_zip_error(member_name: str, exc: Exception) -> None:
        error = f"{member_name}: {exc}"
        extraction_errors.append(error)
        runtime.output.log(
            message(
                "extract_error",
                "Cannot extract {item}: {error}",
                item=member_name,
                error=exc,
            )
        )
        runtime.output.report(
            message("extract_failed", "Cannot extract {item}", item=member_name)
        )

    extract_zip_members_func(
        ifile, paths.unpack_path, on_member=on_zip_member, on_error=on_zip_error
    )
    if extraction_errors:
        return ProjectImportResult.failure("; ".join(extraction_errors))
    runtime.output.log(
        message("archive_extract_complete", "Archive extraction completed")
    )
    script2fs_func(paths.unpack_path)
    if runtime.auto_unpack:
        unpack_func(
            list_auto_unpack_candidates(paths.unpack_path),
            runtime=workflow_runtime or build_import_unpack_runtime(runtime, paths),
        )
    return ProjectImportResult.success(project_name=project_name)


__all__ = ["import_zip_rom"]
