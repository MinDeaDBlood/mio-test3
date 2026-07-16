from __future__ import annotations

import logging

from src.logic.common.messages import message

from .base import ImageHandlerContext


_PREPROCESSOR_TYPES = frozenset({'dtbo', 'boot', 'vendor_boot', 'vbmeta'})


def convert_sparse_if_needed(ctx: ImageHandlerContext, file_type: str) -> str:
    if file_type != 'sparse':
        return file_type
    ctx.output.log(message('processing', 'Processing {item}', item=f'{ctx.partition_name}.img[{file_type}]'))
    try:
        ctx.operations.simg2img(ctx.image_path)
    except (OSError, RuntimeError, ValueError):
        logging.exception(
            'Unpack workflow sparse conversion failed: partition=%s; image_path=%s',
            ctx.partition_name,
            ctx.image_path,
        )
        ctx.output.report(message('operation_failed', 'Operation failed: {item}', item=f'{ctx.partition_name}.img'))
    return ctx.operations.get_type(ctx.image_path)


def run_partition_preprocessors(ctx: ImageHandlerContext, file_type: str) -> bool | None:
    if file_type not in _PREPROCESSOR_TYPES and ctx.partition_name != 'logo':
        return None
    if file_type == 'dtbo':
        return bool(ctx.operations.unpack_dtbo(ctx.partition_name, image_path=ctx.image_path, workflow_runtime=ctx.runtime))
    if file_type in {'boot', 'vendor_boot'}:
        return bool(ctx.operations.unpack_boot(ctx.partition_name, image_path=ctx.image_path, workflow_runtime=ctx.runtime))
    if ctx.partition_name == 'logo':
        try:
            ctx.operations.logo_dumper_cls(ctx.image_path, f'{ctx.work}/{ctx.partition_name}').check_img(ctx.image_path)
        except AssertionError:
            logging.exception(
                'Unpack workflow logo validation failed: partition=%s; image_path=%s',
                ctx.partition_name,
                ctx.image_path,
            )
            return False
        return bool(
            ctx.operations.logo_dump(
                ctx.image_path,
                output_name=ctx.partition_name,
                work_path=ctx.work,
                service_output=ctx.output,
            )
        )
    if file_type == 'vbmeta':
        ctx.output.log(message('patching_avb', 'Patching AVB: {partition}', partition=ctx.partition_name))
        return bool(ctx.operations.vbpatch_cls(ctx.image_path).disavb())
    return None


__all__ = ['convert_sparse_if_needed', 'run_partition_preprocessors']
