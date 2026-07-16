from __future__ import annotations

import logging
import os
import zipfile

from src.core.file_finder import get_all_file_paths
from src.core.file_ops import remove_path
from src.logic.common.messages import message
from src.logic.common.service_output import (
    OutputSeverity,
    ServiceOutput,
    build_service_output,
)


def rmdir(
    path: str,
    quiet: bool = False,
    *,
    output: ServiceOutput | None = None,
) -> int:
    output = output or build_service_output()
    if not path:
        if not quiet:
            output.report(message("project_not_selected", "Project is not selected"))
        return 1
    if not quiet:
        output.log(message("removing", "Removing {item}", item=path))
    try:
        removed = remove_path(path, missing_ok=True)
    except OSError:
        logging.exception("workspace.remove_path_failed: path=%s", path)
        if not quiet:
            output.report(
                message("operation_failed", "Operation failed: {item}", item=path),
                severity=OutputSeverity.ERROR,
            )
        return 1
    if not quiet:
        output.log(
            message("removed", "Removed {item}", item=path)
            if removed
            else message("file_not_found", "File not found: {item}", item=path)
        )
    return 0


def pack_zip(
    input_dir: str | None = None,
    output_zip: str | None = None,
    silent: bool = False,
    *,
    project_name: str | None = None,
    output: ServiceOutput | None = None,
):
    output = output or build_service_output()
    if not input_dir or not output_zip or not project_name:
        raise ValueError("ZIP packing requires input_dir, output_zip and project_name.")
    os.makedirs(os.path.dirname(output_zip), exist_ok=True)
    normalized_output_zip = os.path.abspath(output_zip)
    output.log(message("packing_project", "Packing project: {name}", name=project_name))
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in get_all_file_paths(input_dir):
            file_path = str(file_path)
            if os.path.abspath(file_path) == normalized_output_zip:
                continue
            archive_name = os.path.relpath(file_path, input_dir)
            if not silent:
                output.log(
                    message("adding_file", "Adding file: {item}", item=archive_name)
                )
            archive.write(file_path, arcname=archive_name)
    if os.path.exists(output_zip):
        output.log(
            message("created", "Created: {item}", item=output_zip),
            severity=OutputSeverity.SUCCESS,
        )
    return output_zip


__all__ = ["pack_zip", "rmdir"]
