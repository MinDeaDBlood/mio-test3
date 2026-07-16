"""Low level sparse segment merging.

This module knows how to locate sparse chunks, convert the first chunk with
``simg2img`` and append the remaining raw chunks. It does not know anything
about projects, localization, windows or user notifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import re
from typing import Callable, Protocol

from src.core.process_runner import call
from src.core.android_sparse import is_sparse_image, merge_sparse_overlays

logger = logging.getLogger(__name__)


class ProcessCall(Protocol):
    def __call__(self, command: list[str], *, extra_path: bool, out: bool) -> int: ...


class SparseMergeStatus(str, Enum):
    MERGED = 'merged'
    NO_SEGMENTS = 'no_segments'
    OUTPUT_EXISTS = 'output_exists'


@dataclass(frozen=True)
class SparseMergeResult:
    status: SparseMergeStatus
    output_path: Path
    segment_paths: tuple[Path, ...]


ProgressCallback = Callable[[int], None]


def natural_sort_key(value: str) -> list[str | int]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r'([0-9]+)', value)]


def find_simg2img_executable(tool_bin_path: str | Path) -> Path:
    tool_directory = Path(tool_bin_path)
    if not tool_directory.is_dir():
        raise NotADirectoryError(f'Tool directory does not exist: {tool_directory}')

    for name in ('simg2img.exe', 'simg2img'):
        executable = tool_directory / name
        if executable.is_file():
            return executable

    raise FileNotFoundError(f'simg2img was not found in: {tool_directory}')


def find_sparse_segments(source_directory: str | Path) -> tuple[Path, ...]:
    source = Path(source_directory)
    if not source.is_dir():
        raise NotADirectoryError(f'Source directory does not exist: {source}')

    pattern = re.compile(r'.*(_sparsechunk|sparse_chunk|\.chunk|\.img)\.\d+$')
    segments = [item for item in source.iterdir() if item.is_file() and pattern.match(item.name)]
    segments.sort(key=lambda item: natural_sort_key(item.name))
    return tuple(segments)


def merge_sparse_segments(
    *,
    source_directory: str | Path,
    output_path: str | Path,
    tool_bin_path: str | Path,
    progress_callback: ProgressCallback | None = None,
    process_call: ProcessCall = call,
) -> SparseMergeResult:
    """Merge sparse chunks into one raw image without UI side effects."""
    source = Path(source_directory)
    output = Path(output_path)
    segments = find_sparse_segments(source)

    if output.exists():
        return SparseMergeResult(SparseMergeStatus.OUTPUT_EXISTS, output, segments)
    if not segments:
        return SparseMergeResult(SparseMergeStatus.NO_SEGMENTS, output, segments)

    total_size = sum(segment.stat().st_size for segment in segments)
    if total_size <= 0:
        raise ValueError('Sparse segments have zero total size')

    if all(is_sparse_image(segment) for segment in segments):
        merge_sparse_overlays(segments, output, progress_callback=progress_callback)
        logger.info('Merged %d sparse overlay segments into %s', len(segments), output)
        return SparseMergeResult(SparseMergeStatus.MERGED, output, segments)

    executable = find_simg2img_executable(tool_bin_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial_output = output.with_name(f'{output.name}.part')
    if partial_output.exists():
        raise FileExistsError(f'Partial output already exists: {partial_output}')

    first_segment = segments[0]
    processed_size = 0
    try:
        command = [str(executable), str(first_segment), str(partial_output)]
        return_code = process_call(command, extra_path=False, out=False)
        if return_code != 0:
            raise RuntimeError(
                f'simg2img failed with exit code {return_code} for {first_segment.name}'
            )

        processed_size += first_segment.stat().st_size
        if progress_callback is not None:
            progress_callback(int(processed_size * 100 / total_size))

        with partial_output.open('ab') as output_stream:
            for segment in segments[1:]:
                with segment.open('rb') as input_stream:
                    while block := input_stream.read(1024 * 1024):
                        output_stream.write(block)
                processed_size += segment.stat().st_size
                if progress_callback is not None:
                    progress_callback(int(processed_size * 100 / total_size))

        partial_output.replace(output)
    except Exception:
        partial_output.unlink(missing_ok=True)
        raise

    if progress_callback is not None:
        progress_callback(100)
    logger.info('Merged %d sparse segments into %s', len(segments), output)
    return SparseMergeResult(SparseMergeStatus.MERGED, output, segments)


__all__ = [
    'ProcessCall',
    'ProgressCallback',
    'SparseMergeResult',
    'SparseMergeStatus',
    'find_simg2img_executable',
    'find_sparse_segments',
    'merge_sparse_segments',
    'natural_sort_key',
]
