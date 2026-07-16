from __future__ import annotations

from typing import Any

from src.logic.common.messages import message
from src.logic.projects.unpack.workflow.image_handlers import (
    ImageHandlerContext,
    ImageHandlerRegistry,
    ImageProcessingOperations,
)


def _drop_stale_partition_entry(parts: dict, partition_name: str) -> None:
    if partition_name in parts:
        parts.pop(partition_name)


def _record_partition_type(parts: dict, partition_name: str, image_path: str, operations: ImageProcessingOperations) -> str:
    file_type = operations.get_type(image_path)
    if file_type != 'sparse':
        parts[partition_name] = file_type
    return file_type


def _build_context(
    *,
    runtime: Any,
    work: str,
    partition_name: str,
    image_path: str,
    parts: dict,
    json_edit: Any,
    operations: ImageProcessingOperations,
) -> ImageHandlerContext:
    return ImageHandlerContext(
        runtime=runtime,
        work=work,
        partition_name=partition_name,
        image_path=image_path,
        parts=parts,
        json_edit=json_edit,
        output=operations.runtime_output(runtime),
        operations=operations,
    )


def process_existing_image(
    runtime: Any,
    work: str,
    partition_name: str,
    image_path: str,
    parts: dict,
    json_edit: Any,
    *,
    operations: ImageProcessingOperations,
    registry: ImageHandlerRegistry | None = None,
) -> bool:
    registry = registry or ImageHandlerRegistry.default()
    ctx = _build_context(
        runtime=runtime,
        work=work,
        partition_name=partition_name,
        image_path=image_path,
        parts=parts,
        json_edit=json_edit,
        operations=operations,
    )

    _drop_stale_partition_entry(parts, partition_name)
    file_type = _record_partition_type(parts, partition_name, ctx.image_path, operations)
    preprocessor_result = registry.run_preprocessors(ctx, file_type)
    if preprocessor_result is not None:
        return preprocessor_result

    file_type = registry.convert_sparse(ctx, operations.get_type(ctx.image_path))
    if file_type == 'sparse':
        return False
    parts[partition_name] = file_type
    ctx.output.log(message('processing', 'Processing {item}', item=f'{partition_name}.img[{file_type}]'))

    container_result = registry.handle_container(ctx, file_type)
    if container_result is not None:
        return container_result
    extractor_result = registry.handle_extractor(ctx, file_type)
    return bool(extractor_result)


__all__ = ['ImageHandlerRegistry', 'ImageProcessingOperations', 'process_existing_image']
