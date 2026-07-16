from __future__ import annotations

import os

from src.logic.common.messages import message

from .base import ImageHandlerContext


_EXTRACTABLE_TYPES = frozenset({'ext', 'romfs', 'rkfw', 'rkaf', 'guoke_logo', 'splash', 'gpt', 'erofs', 'f2fs', 'amlogic', 'unknown'})


def _directory_has_content(path: str) -> bool:
    return os.path.isdir(path) and any(os.scandir(path))


def handle_extracted_image_type(ctx: ImageHandlerContext, file_type: str) -> bool | None:
    if file_type not in _EXTRACTABLE_TYPES:
        return None
    if file_type == 'ext':
        return bool(ctx.operations.extract_ext_image(ctx.runtime, ctx.work, ctx.partition_name, ctx.parts, image_path=ctx.image_path))
    if file_type == 'romfs':
        ctx.operations.romfs_parse_cls(ctx.image_path).extract(ctx.work)
        return os.path.isdir(os.path.join(ctx.work, ctx.partition_name))
    if file_type in {'rkfw', 'rkaf'}:
        return ctx.operations.call(['afptool', 'unpack', ctx.image_path, ctx.work]) == 0
    if file_type == 'guoke_logo':
        target_path = os.path.join(ctx.work, ctx.partition_name)
        ctx.operations.guoke_logo_cls().unpack(ctx.image_path, target_path)
        return _directory_has_content(target_path)
    if file_type == 'splash':
        return bool(ctx.operations.extract_splash_image(ctx.runtime, ctx.work, ctx.partition_name, image_path=ctx.image_path))
    if file_type == 'gpt':
        return bool(ctx.operations.extract_gpt_image(ctx.runtime, ctx.work, ctx.partition_name, image_path=ctx.image_path))
    if file_type == 'erofs':
        return bool(ctx.operations.extract_erofs_image(ctx.runtime, ctx.work, ctx.partition_name, image_path=ctx.image_path))
    if file_type == 'f2fs':
        return bool(ctx.operations.extract_f2fs_image(ctx.runtime, ctx.work, ctx.partition_name, image_path=ctx.image_path))
    if file_type == 'amlogic':
        ctx.operations.aml_main(ctx.image_path, ctx.work)
        return True
    if file_type == 'unknown' and ctx.operations.is_empty_image(ctx.image_path):
        ctx.output.log(message('extract_complete', 'Extraction completed'))
        return True
    return False


__all__ = ['handle_extracted_image_type']
