from __future__ import annotations

import os
from shutil import copy2
from typing import Callable

from src.core.file_types import gettype
from src.logic.common.messages import message
from src.logic.projects.import_flow.auto_unpack import list_auto_unpack_candidates
from src.logic.projects.import_flow.models import ProjectImportResult
from src.logic.projects.import_flow.script_fs import script2fs as default_script2fs
from src.logic.projects.import_flow.workspace import (
    build_import_unpack_runtime,
    ensure_import_workspace,
)


def _preserve_source(ifile: str, input_path: str, runtime) -> None:
    try:
        copy2(ifile, input_path)
    except OSError as exc:
        runtime.output.log(
            message("copy_failed", "Cannot copy {item}: {error}", item=ifile, error=exc)
        )


def handle_ozip(
    ifile: str,
    *,
    runtime,
    unpackrom_func: Callable[..., ProjectImportResult],
) -> ProjectImportResult:
    from src.core import ozipdecrypt

    ozipdecrypt.main(ifile)
    decrypted = os.path.dirname(ifile) + os.sep + os.path.basename(ifile)[:-4] + "zip"
    if not os.path.exists(decrypted):
        return ProjectImportResult.failure(f"Cannot decrypt {ifile}.")
    try:
        return unpackrom_func(decrypted, runtime=runtime)
    finally:
        if os.path.exists(decrypted):
            os.remove(decrypted)


def handle_kdz(ifile: str, *, runtime) -> ProjectImportResult:
    from src.core.unkdz import KDZFileTools
    from src.core.undz import DZFileTools

    project_name = os.path.splitext(os.path.basename(ifile))[0]
    paths = ensure_import_workspace(runtime.project_manager, project_name)
    _preserve_source(ifile, paths.input_path, runtime)
    KDZFileTools(ifile, paths.unpack_path, extract_all=True)
    for name in os.listdir(paths.unpack_path):
        file_path = os.path.join(paths.unpack_path, name)
        if (
            os.path.isfile(file_path)
            and name.endswith(".dz")
            and gettype(file_path) == "dz"
        ):
            DZFileTools(file_path, paths.unpack_path, extract_all=True)
    return ProjectImportResult.success(project_name=project_name)


def handle_ofp(
    ifile: str,
    *,
    runtime,
    ofp_mtk_decrypt,
    ofp_qc_decrypt,
    script2fs_func: Callable[[str], object] = default_script2fs,
) -> ProjectImportResult:
    if runtime.ofp_mtk_decrypt is None:
        raise ValueError("OFP import requires an explicit decryption mode.")
    project_name = os.path.splitext(os.path.basename(ifile))[0]
    paths = ensure_import_workspace(runtime.project_manager, project_name)
    _preserve_source(ifile, paths.input_path, runtime)
    if runtime.ofp_mtk_decrypt:
        ofp_mtk_decrypt.main(ifile, paths.unpack_path)
    else:
        ofp_qc_decrypt.main(ifile, paths.unpack_path)
        script2fs_func(paths.unpack_path)
    return ProjectImportResult.success(project_name=project_name)


def handle_ops(ifile: str, *, runtime) -> ProjectImportResult:
    from src.core import opscrypto

    project_name = os.path.basename(ifile).split(".")[0]
    paths = ensure_import_workspace(runtime.project_manager, project_name)
    _preserve_source(ifile, paths.input_path, runtime)
    args = {
        "decrypt": True,
        "<filename>": ifile,
        "outdir": paths.unpack_path,
    }
    opscrypto.main(args)
    return ProjectImportResult.success(project_name=project_name)


def handle_pac(
    ifile: str,
    *,
    runtime,
    unpack_func: Callable[..., object],
    workflow_runtime: object | None = None,
) -> ProjectImportResult:
    from src.core.unpac import MODE as PACMODE, unpac

    project_name = os.path.splitext(os.path.basename(ifile))[0]
    paths = ensure_import_workspace(runtime.project_manager, project_name)
    _preserve_source(ifile, paths.input_path, runtime)
    unpac(ifile, paths.unpack_path, PACMODE.EXTRACT)
    if runtime.auto_unpack:
        unpack_func(
            list_auto_unpack_candidates(paths.unpack_path),
            runtime=workflow_runtime or build_import_unpack_runtime(runtime, paths),
        )
    return ProjectImportResult.success(project_name=project_name)


def handle_ntpi(ifile: str, *, runtime) -> ProjectImportResult:
    from src.core.ntpiutils import extractor as ntpiextractor, parser as ntpiparser

    project_name = os.path.splitext(os.path.basename(ifile))[0]
    paths = ensure_import_workspace(runtime.project_manager, project_name)
    _preserve_source(ifile, paths.input_path, runtime)
    os.makedirs(paths.unpack_path, exist_ok=True)
    ntpiparser.parse_ntpi_file(ifile, paths.unpack_path)
    ntpiextractor.stage2_extract_files(paths.unpack_path, paths.unpack_path)
    return ProjectImportResult.success(project_name=project_name)


__all__ = [
    "handle_kdz",
    "handle_ntpi",
    "handle_ofp",
    "handle_ops",
    "handle_ozip",
    "handle_pac",
]
