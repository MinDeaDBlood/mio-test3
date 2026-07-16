from __future__ import annotations

import os
from typing import Any

from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity, ServiceOutput
from src.logic.projects.boot_images.runtime_context import (
    build_runtime_context as build_boot_runtime_context,
)
from src.logic.projects.dtbo.runtime_context import build_dtbo_runtime_context
from src.logic.projects.logo.service import (
    build_runtime_context as build_logo_runtime_context,
)

VBMETA_IMAGE_NAMES: tuple[str, ...] = (
    "vbmeta.img",
    "vbmeta_system.img",
    "vbmeta_vendor.img",
)

_BOOTLIKE_PARTITIONS: frozenset[str] = frozenset({"boot", "vendor_boot"})


def patch_vbmeta_images(
    work: str, patch_enabled: bool, deps: Any, *, output: ServiceOutput
) -> None:
    if not patch_enabled:
        return
    for image_name in VBMETA_IMAGE_NAMES:
        image_path = deps.findfile_func(image_name, work)
        if deps.gettype_func(image_path) == "vbmeta":
            output.log(
                message("patching_image", "Patching image: {path}", path=image_path),
                severity=OutputSeverity.INFO,
            )
            deps.vbpatch_factory(image_path).disavb()


def pack_special_partition(
    partition_name: str, work: str, runtime: Any, deps: Any
) -> bool:
    if partition_name in _BOOTLIKE_PARTITIONS:
        boot_runtime = build_boot_runtime_context(
            input_path=runtime.input_path,
            work_path=runtime.work_path,
            output_path=runtime.output_path,
            tool_bin=runtime.tool_bin,
            magisk_not_decompress=runtime.magisk_not_decompress,
            boot_skip_ramdisk=runtime.boot_skip_ramdisk,
            output=runtime.output,
        )
        deps.repack_boot_func(partition_name, runtime=boot_runtime)
        return True
    if partition_name == "dtbo":
        dtbo_runtime = build_dtbo_runtime_context(
            work_path=runtime.work_path,
            output_path=runtime.output_path,
            output=runtime.output,
        )
        deps.pack_dtbo_func(runtime=dtbo_runtime)
        return True
    if partition_name == "splash":
        deps.splash_repack_func(
            os.path.join(work, partition_name),
            os.path.join(work, f"{partition_name}.img"),
        )
        return True
    if partition_name == "logo":
        logo_runtime = build_logo_runtime_context(
            work_path=runtime.work_path,
            output=runtime.output,
        )
        deps.logo_pack_func(runtime=logo_runtime)
        return True
    if partition_name == "guoke_logo":
        deps.guoke_logo_cls().pack(
            os.path.join(work, partition_name),
            os.path.join(work, f"{partition_name}.img"),
        )
        return True
    return False


__all__ = ["VBMETA_IMAGE_NAMES", "pack_special_partition", "patch_vbmeta_images"]
