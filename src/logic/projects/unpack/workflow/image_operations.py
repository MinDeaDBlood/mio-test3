from __future__ import annotations

import os
import shutil
from typing import Any

from src.core import lpunpack
from src.core.aml_image import main as aml_main
from src.core.file_types import gettype, is_empty_img
from src.core.logo import GuoKeLogo, LogoDumper
from src.core.process_runner import call
from src.core.romfs_parse import RomfsParse
from src.core.sparse_tools import simg2img
from src.core.vbmeta import Vbpatch
from src.logic.projects.unpack.runtime_context import UnpackWorkflowRuntimeContext
from src.logic.projects.unpack.workflow.image_adapters import dump_logo, runtime_output, unpack_boot, unpack_dtbo
from src.logic.projects.unpack.workflow.image_extractors import (
    extract_erofs_image,
    extract_ext_image,
    extract_f2fs_image,
    extract_gpt_image,
    extract_splash_image,
)
from src.logic.projects.unpack.workflow.image_processing import (
    ImageProcessingOperations,
    process_existing_image as _process_existing_image,
)
from src.logic.projects.unpack.workflow.source_handlers import metadata_file_valid, normalize_super_outputs


def build_image_processing_operations() -> ImageProcessingOperations:
    return ImageProcessingOperations(
        get_type=gettype,
        is_empty_image=is_empty_img,
        simg2img=simg2img,
        lpunpack_get_info=lpunpack.get_info,
        lpunpack_unpack=lpunpack.unpack,
        normalize_super_outputs=normalize_super_outputs,
        unpack_dtbo=unpack_dtbo,
        unpack_boot=unpack_boot,
        logo_dump=dump_logo,
        logo_dumper_cls=LogoDumper,
        vbpatch_cls=Vbpatch,
        romfs_parse_cls=RomfsParse,
        guoke_logo_cls=GuoKeLogo,
        aml_main=aml_main,
        call=call,
        extract_ext_image=extract_ext_image,
        extract_erofs_image=extract_erofs_image,
        extract_f2fs_image=extract_f2fs_image,
        extract_gpt_image=extract_gpt_image,
        extract_splash_image=extract_splash_image,
        runtime_output=runtime_output,
    )


def resolve_image_for_processing(source: str, work: str, partition_name: str) -> str | None:
    work_image = os.path.join(work, f'{partition_name}.img')
    if metadata_file_valid(work_image):
        return work_image
    source_image = os.path.join(source, f'{partition_name}.img')
    if not metadata_file_valid(source_image):
        return None
    if gettype(source_image) == 'sparse':
        os.makedirs(work, exist_ok=True)
        shutil.copy2(source_image, work_image)
        return work_image
    return source_image


def process_partition_image(
    runtime: UnpackWorkflowRuntimeContext,
    work: str,
    partition_name: str,
    image_path: str,
    parts: dict,
    json_edit: Any,
) -> bool:
    return _process_existing_image(
        runtime,
        work,
        partition_name,
        image_path,
        parts,
        json_edit,
        operations=build_image_processing_operations(),
    )


__all__ = [
    'build_image_processing_operations',
    'process_partition_image',
    'resolve_image_for_processing',
    'runtime_output',
]
