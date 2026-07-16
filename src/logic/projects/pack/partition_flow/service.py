from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Callable

from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity
from src.logic.projects.pack.partition_special import (
    pack_special_partition,
    patch_vbmeta_images,
)
from src.logic.projects.pack.partition_flow.filesystem_handlers import (
    PACKABLE_FILESYSTEM_TYPES,
    pack_filesystem_partition,
)

from .models import PackPartitionRequest


@dataclass(frozen=True)
class PackPartitionDependencies:
    json_edit_cls: type
    fspatch_main: Callable
    contextpatch_main: Callable
    contextpatch_scan_context: Callable
    guoke_logo_cls: type
    logo_pack_func: Callable
    pack_dtbo_func: Callable
    repack_boot_func: Callable
    splash_repack_func: Callable
    mkerofs_func: Callable
    make_f2fs_func: Callable
    make_ext4fs_func: Callable
    mke2fs_func: Callable
    apply_output_format_func: Callable
    rdi_func: Callable
    remove_duplicate_func: Callable
    vbpatch_factory: Callable
    findfile_func: Callable
    gettype_func: Callable


def load_parts_dict(work_path: str, json_edit_cls) -> dict:
    return json_edit_cls(os.path.join(work_path, "config", "parts_info")).read()


def has_packable_partitions(chosen_parts: list[str], parts_dict: dict) -> bool:
    for partition in chosen_parts:
        if partition not in parts_dict.keys():
            parts_dict[partition] = "unknown"
        if parts_dict[partition] in PACKABLE_FILESYSTEM_TYPES:
            return True
    return False


def pack_selected_partitions(
    request: PackPartitionRequest, runtime, deps: PackPartitionDependencies
) -> bool | None:
    if not runtime.project_selected:
        return False
    work = runtime.work_path
    parts_dict = load_parts_dict(runtime.work_path, deps.json_edit_cls)
    patch_vbmeta_images(work, request.patch_vbmeta, deps, output=runtime.output)
    for partition_name in request.chosen_parts:
        partition_name = os.path.basename(partition_name)
        if partition_name not in parts_dict.keys():
            parts_dict[partition_name] = "unknown"
        if parts_dict[partition_name] in PACKABLE_FILESYSTEM_TYPES:
            if not pack_filesystem_partition(
                work=work,
                partition_name=partition_name,
                request=request,
                parts_dict=parts_dict,
                runtime=runtime,
                deps=deps,
            ):
                return False
            continue
        if pack_special_partition(partition_name, work, runtime, deps):
            continue
        if os.path.exists(os.path.join(work, partition_name)):
            runtime.output.log(
                message(
                    "unsupported_partition_type",
                    "Unsupported {partition}:{type}",
                    partition=partition_name,
                    type=parts_dict[partition_name],
                ),
                severity=OutputSeverity.WARNING,
            )
        logging.warning(f"{partition_name} Not Supported.")
    return True


__all__ = [
    "PackPartitionDependencies",
    "PackPartitionRequest",
    "has_packable_partitions",
    "load_parts_dict",
    "pack_selected_partitions",
]
