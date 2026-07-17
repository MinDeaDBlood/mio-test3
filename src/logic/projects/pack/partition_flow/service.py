from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Callable

from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity
from src.logic.projects.pack.partition_flow.filesystem_handlers import (
    PACKABLE_FILESYSTEM_TYPES,
    pack_filesystem_partition,
)
from src.logic.projects.pack.partition_special import (
    pack_special_partition,
    patch_vbmeta_images,
)

from .models import PackPartitionRequest

logger = logging.getLogger(__name__)


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
    parts_info_path = os.path.join(work_path, "config", "parts_info")
    logger.debug("partition_pack.parts_info_read: path=%s", parts_info_path)
    parts = json_edit_cls(parts_info_path).read()
    logger.info(
        "partition_pack.parts_info_loaded: path=%s entries=%s",
        parts_info_path,
        len(parts),
    )
    return parts


def has_packable_partitions(chosen_parts: list[str], parts_dict: dict) -> bool:
    for partition in chosen_parts:
        if partition not in parts_dict:
            parts_dict[partition] = "unknown"
        if parts_dict[partition] in PACKABLE_FILESYSTEM_TYPES:
            return True
    return False


def pack_selected_partitions(
    request: PackPartitionRequest, runtime, deps: PackPartitionDependencies
) -> bool | None:
    if not runtime.project_selected:
        logger.warning("partition_pack.logic_rejected: reason=project_not_selected")
        return False

    work = runtime.work_path
    logger.info(
        "partition_pack.logic_started: work=%s output=%s input=%s selected=%r",
        work,
        runtime.output_path,
        runtime.input_path,
        request.chosen_parts,
    )
    parts_dict = load_parts_dict(runtime.work_path, deps.json_edit_cls)
    patch_vbmeta_images(work, request.patch_vbmeta, deps, output=runtime.output)

    completed: list[str] = []
    for index, selected_name in enumerate(request.chosen_parts, start=1):
        partition_name = os.path.basename(selected_name)
        partition_type = parts_dict.get(partition_name, "unknown")
        parts_dict.setdefault(partition_name, partition_type)
        source_path = os.path.join(work, partition_name)
        logger.info(
            "partition_pack.partition_started: index=%s total=%s partition=%s "
            "type=%s source=%s output=%s",
            index,
            len(request.chosen_parts),
            partition_name,
            partition_type,
            source_path,
            runtime.output_path,
        )

        if partition_type in PACKABLE_FILESYSTEM_TYPES:
            success = pack_filesystem_partition(
                work=work,
                partition_name=partition_name,
                request=request,
                parts_dict=parts_dict,
                runtime=runtime,
                deps=deps,
            )
            if not success:
                logger.error(
                    "partition_pack.partition_failed: partition=%s type=%s stage=filesystem",
                    partition_name,
                    parts_dict.get(partition_name, partition_type),
                )
                return False
            completed.append(partition_name)
            logger.info(
                "partition_pack.partition_completed: partition=%s type=%s stage=filesystem",
                partition_name,
                parts_dict.get(partition_name, partition_type),
            )
            continue

        if pack_special_partition(partition_name, work, runtime, deps):
            completed.append(partition_name)
            logger.info(
                "partition_pack.partition_dispatched: partition=%s type=%s stage=special",
                partition_name,
                partition_type,
            )
            continue

        if os.path.exists(source_path):
            runtime.output.log(
                message(
                    "unsupported_partition_type",
                    "Unsupported {partition}:{type}",
                    partition=partition_name,
                    type=partition_type,
                ),
                severity=OutputSeverity.WARNING,
            )
        logger.warning(
            "partition_pack.partition_unsupported: partition=%s type=%s source_exists=%s",
            partition_name,
            partition_type,
            os.path.exists(source_path),
        )

    logger.info(
        "partition_pack.logic_completed: selected=%r completed=%r output=%s",
        request.chosen_parts,
        completed,
        runtime.output_path,
    )
    return True


__all__ = [
    "PackPartitionDependencies",
    "PackPartitionRequest",
    "has_packable_partitions",
    "load_parts_dict",
    "pack_selected_partitions",
]
