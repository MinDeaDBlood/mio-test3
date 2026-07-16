from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.core.android_sparse import split_raw_image_to_sparse_parts
from src.core.file_types import gettype

from .models import SplitSuperRequest, SplitSuperResult


def validate_split_super_request(request: SplitSuperRequest) -> None:
    source = Path(request.input_path.strip())
    output = Path(request.output_directory.strip())
    if not request.input_path.strip():
        raise ValueError('Input image is required')
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f'Input image was not found or is empty: {source}')
    if gettype(str(source)) != 'super':
        raise ValueError(f'Input image is not a raw super image: {source}')
    if not request.output_directory.strip():
        raise ValueError('Output directory is required')
    if output.exists() and not output.is_dir():
        raise NotADirectoryError(f'Output path is not a directory: {output}')
    if request.part_count < 2:
        raise ValueError('Part count must be at least 2')
    if request.block_size <= 0 or request.block_size % 4:
        raise ValueError('Block size must be a positive multiple of 4')
    try:
        request.suffix_format % 0
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Invalid suffix format: {request.suffix_format!r}') from exc


def execute_split_super(
    request: SplitSuperRequest,
    *,
    progress_callback: Callable[[int], None] | None = None,
) -> SplitSuperResult:
    validate_split_super_request(request)
    result = split_raw_image_to_sparse_parts(
        request.input_path,
        request.output_directory,
        part_count=request.part_count,
        block_size=request.block_size,
        suffix_format=request.suffix_format,
        keep_existing=request.keep_existing,
        progress_callback=progress_callback,
    )
    return SplitSuperResult(
        source_path=result.source_path,
        output_paths=result.output_paths,
        block_size=result.block_size,
        total_blocks=result.total_blocks,
    )


__all__ = ['execute_split_super', 'validate_split_super_request']
