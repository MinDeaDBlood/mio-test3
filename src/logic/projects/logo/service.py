from __future__ import annotations

import os
from dataclasses import dataclass

from src.core.file_finder import findfile
from src.logic.common.messages import message
from src.core.logo import LogoDumper
from src.logic.common.service_output import ServiceOutput
from src.logic.projects.common.fs_service import re_folder
from src.logic.projects.common.workspace_service import rmdir


@dataclass(frozen=True)
class LogoRuntimeContext:
    work_path: str
    output: ServiceOutput


def build_runtime_context(
    *, work_path: str, output: ServiceOutput
) -> LogoRuntimeContext:
    return LogoRuntimeContext(work_path=str(work_path), output=output)


def _require_runtime(runtime: LogoRuntimeContext | None) -> LogoRuntimeContext:
    if runtime is None:
        raise ValueError("Logo operation requires an explicit LogoRuntimeContext.")
    return runtime


def dump_logo(
    file_path: str,
    output: str | None = None,
    output_name: str = "logo",
    *,
    runtime: LogoRuntimeContext | None = None,
    exists_func=os.path.exists,
    re_folder_func=re_folder,
    dumper_cls=LogoDumper,
) -> bool:
    runtime = _require_runtime(runtime)
    output_root = output if output is not None else runtime.work_path
    if not exists_func(file_path):
        runtime.output.report(
            message("file_not_found", "File not found: {item}", item=output_name)
        )
        return False
    target_dir = os.path.join(output_root, output_name)
    re_folder_func(target_dir)
    dumper_cls(file_path, target_dir).unpack()
    return True


def pack_logo(
    origin_logo: str | None = None,
    *,
    runtime: LogoRuntimeContext | None = None,
    exists_func=os.path.exists,
    findfile_func=findfile,
    remove_func=os.remove,
    replace_func=os.replace,
    rmdir_func=rmdir,
    dumper_cls=LogoDumper,
) -> int:
    runtime = _require_runtime(runtime)
    work = runtime.work_path
    origin_logo = origin_logo or findfile_func("logo.img", work)
    logo_dir = os.path.join(work, "logo")
    temp_output = os.path.join(work, "logo-new.img")
    if not exists_func(logo_dir) or not origin_logo or not exists_func(origin_logo):
        runtime.output.log(message("operation_failed", "Operation failed"))
        return 1
    dumper_cls(origin_logo, temp_output, logo_dir).repack()
    remove_func(origin_logo)
    replace_func(temp_output, origin_logo)
    rmdir_func(logo_dir)
    return 0


__all__ = ["LogoRuntimeContext", "build_runtime_context", "dump_logo", "pack_logo"]
