from __future__ import annotations

from importlib import import_module
import os
from shutil import copy2

from src.core import tarsafe
from src.core.file_types import gettype
from src.logic.common.messages import message
from src.logic.projects.common.runtime_context import ProjectImportRuntimeContext
from src.logic.projects.import_flow.archive_handlers import (
    extract_gzip_payload,
    strip_gzip_suffix,
)
from src.logic.projects.import_flow.format_handlers import (
    handle_kdz,
    handle_ntpi,
    handle_ofp,
    handle_ops,
    handle_ozip,
    handle_pac,
)
from src.logic.projects.import_flow.generic_file_import import import_known_file
from src.logic.projects.import_flow.models import ProjectImportResult
from src.logic.projects.import_flow.project_folder_import import import_project_folder
from src.logic.projects.import_flow.script_fs import script2fs
from src.logic.projects.import_flow.workspace import (
    ensure_import_workspace,
)
from src.logic.projects.import_flow.zip_import import import_zip_rom
from src.logic.projects.unpack.workflow.service import unpack


class _LazyMainProxy:
    def __init__(self, module_name: str):
        self._module_name = module_name
        self.main = self._call_main

    def _load(self):
        return import_module(self._module_name)

    def _call_main(self, *args, **kwargs):
        return self._load().main(*args, **kwargs)


ofp_mtk_decrypt = _LazyMainProxy("src.core.ofp_mtk_decrypt")
ofp_qc_decrypt = _LazyMainProxy("src.core.ofp_qc_decrypt")


def _preserve_input_file(path: str, input_path: str, output=None) -> None:
    try:
        os.makedirs(input_path, exist_ok=True)
        copy2(path, input_path)
    except OSError as exc:
        if output is not None:
            output.log(
                message(
                    "copy_failed", "Cannot copy {item}: {error}", item=path, error=exc
                )
            )


def copy_project(
    dir_path: str, *, runtime: ProjectImportRuntimeContext | None = None
) -> ProjectImportResult:
    if runtime is None:
        raise ValueError(
            "Project import requires an explicit ProjectImportRuntimeContext."
        )
    if os.path.isfile(dir_path):
        return unpackrom(dir_path, runtime=runtime)
    return import_project_folder(dir_path, runtime=runtime)


def unpackrom(
    ifile: str, *, runtime: ProjectImportRuntimeContext | None = None
) -> ProjectImportResult:
    if runtime is None:
        raise ValueError(
            "Project import requires an explicit ProjectImportRuntimeContext."
        )
    ftype = gettype(ifile)
    runtime.output.log(
        message(
            "file_detected",
            "Detected file {path} with type {type}",
            path=ifile,
            type=ftype,
        )
    )

    if ftype == "gzip":
        runtime.output.log(message("processing", "Processing {item}", item=ifile))
        old_project_name = os.path.splitext(os.path.basename(ifile))[0]
        paths = ensure_import_workspace(runtime.project_manager, old_project_name)
        _preserve_input_file(ifile, paths.input_path, runtime.output)
        output_file = os.path.join(paths.unpack_path, strip_gzip_suffix(ifile))
        extract_gzip_payload(ifile, output_file)
        result = unpackrom(output_file, runtime=runtime)
        if (
            result.project_name
            and result.project_name != old_project_name
            and runtime.project_manager.exist(old_project_name)
        ):
            runtime.project_manager.remove(old_project_name)
        return result
    if ftype == "ozip":
        return handle_ozip(ifile, runtime=runtime, unpackrom_func=unpackrom)
    if ftype == "tar":
        project_name = os.path.splitext(os.path.basename(ifile))[0]
        paths = ensure_import_workspace(runtime.project_manager, project_name)
        _preserve_input_file(ifile, paths.input_path, runtime.output)
        with tarsafe.TarSafe(ifile) as archive:
            archive.extractall(paths.unpack_path)
        return ProjectImportResult.success(project_name=project_name)
    if ftype == "kdz":
        return handle_kdz(ifile, runtime=runtime)
    if os.path.splitext(ifile)[1].lower() == ".ofp":
        return handle_ofp(
            ifile,
            runtime=runtime,
            ofp_mtk_decrypt=ofp_mtk_decrypt,
            ofp_qc_decrypt=ofp_qc_decrypt,
            script2fs_func=script2fs,
        )
    if os.path.splitext(ifile)[1].lower() == ".ops":
        return handle_ops(ifile, runtime=runtime)
    if ftype == "pac":
        return handle_pac(ifile, runtime=runtime, unpack_func=unpack)
    if ftype == "NTPI":
        return handle_ntpi(ifile, runtime=runtime)
    if ftype == "zip":
        return import_zip_rom(
            ifile,
            runtime=runtime,
            unpack_func=unpack,
            script2fs_func=script2fs,
        )
    if ftype != "unknown":
        return import_known_file(ifile, runtime=runtime, unpack_func=unpack)
    runtime.output.log(
        message("unsupported_format", "Unsupported format: {format}", format=ftype)
    )
    return ProjectImportResult.failure(f"Unsupported format: {ftype}")


__all__ = ["copy_project", "script2fs", "unpackrom"]
