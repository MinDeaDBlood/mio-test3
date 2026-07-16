from __future__ import annotations

import os

from .base import ImageHandlerContext


def _container_output_dir(ctx: ImageHandlerContext) -> str:
    return ctx.runtime.input_path


def handle_known_container(ctx: ImageHandlerContext, file_type: str) -> bool | None:
    if file_type != 'super':
        return None
    output_dir = _container_output_dir(ctx)
    ctx.parts['super_info'] = ctx.operations.lpunpack_get_info(ctx.image_path)
    ctx.operations.lpunpack_unpack(ctx.image_path, output_dir)
    ctx.operations.normalize_super_outputs(output_dir)
    extracted_images = [
        entry
        for entry in os.listdir(output_dir)
        if entry.endswith('.img')
        and entry != os.path.basename(ctx.image_path)
        and os.path.getsize(os.path.join(output_dir, entry)) > 0
    ]
    if not extracted_images:
        return False
    ctx.json_edit.write(ctx.parts)
    ctx.parts.clear()
    return True


__all__ = ['handle_known_container']
