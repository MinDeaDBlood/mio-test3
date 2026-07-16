from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import os
import re
import struct
import tempfile
from typing import BinaryIO, Callable, Iterable

SPARSE_HEADER_MAGIC = 0xED26FF3A
SPARSE_MAJOR_VERSION = 1
CHUNK_TYPE_RAW = 0xCAC1
CHUNK_TYPE_FILL = 0xCAC2
CHUNK_TYPE_DONT_CARE = 0xCAC3
CHUNK_TYPE_CRC32 = 0xCAC4
SPARSE_HEADER_SIZE = 28
CHUNK_HEADER_SIZE = 12
_COPY_BUFFER_SIZE = 1024 * 1024
_HEADER = struct.Struct('<IHHHHIIII')
_CHUNK = struct.Struct('<HHII')


class SparseImageError(ValueError):
    """Raised when an Android sparse image is malformed."""


@dataclass(frozen=True)
class SparseHeader:
    block_size: int
    total_blocks: int
    total_chunks: int
    file_header_size: int
    chunk_header_size: int


@dataclass(frozen=True)
class SparseSplitResult:
    source_path: Path
    output_paths: tuple[Path, ...]
    block_size: int
    total_blocks: int


def parse_size_suffix(value: str) -> int:
    match = re.fullmatch(r'\s*([0-9]+)\s*([KMG]?)\s*', value, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f'Invalid size: {value!r}')
    amount = int(match.group(1))
    factor = {'': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3}[match.group(2).upper()]
    return amount * factor


def is_sparse_image(path: str | Path) -> bool:
    source = Path(path)
    if not source.is_file() or source.stat().st_size < 4:
        return False
    with source.open('rb') as stream:
        return stream.read(4) == struct.pack('<I', SPARSE_HEADER_MAGIC)


def read_sparse_header(stream: BinaryIO) -> SparseHeader:
    raw = stream.read(SPARSE_HEADER_SIZE)
    if len(raw) != SPARSE_HEADER_SIZE:
        raise SparseImageError('Sparse image header is truncated')
    magic, major, _minor, file_header_size, chunk_header_size, block_size, total_blocks, total_chunks, _checksum = _HEADER.unpack(raw)
    if magic != SPARSE_HEADER_MAGIC:
        raise SparseImageError('Android sparse magic was not found')
    if major != SPARSE_MAJOR_VERSION:
        raise SparseImageError(f'Unsupported sparse major version: {major}')
    if file_header_size < SPARSE_HEADER_SIZE:
        raise SparseImageError(f'Invalid sparse file header size: {file_header_size}')
    if chunk_header_size < CHUNK_HEADER_SIZE:
        raise SparseImageError(f'Invalid sparse chunk header size: {chunk_header_size}')
    if block_size <= 0 or block_size % 4:
        raise SparseImageError(f'Invalid sparse block size: {block_size}')
    if total_blocks <= 0 or total_chunks <= 0:
        raise SparseImageError('Sparse image declares no blocks or chunks')
    if file_header_size > SPARSE_HEADER_SIZE:
        extra = stream.read(file_header_size - SPARSE_HEADER_SIZE)
        if len(extra) != file_header_size - SPARSE_HEADER_SIZE:
            raise SparseImageError('Sparse extended file header is truncated')
    return SparseHeader(
        block_size=block_size,
        total_blocks=total_blocks,
        total_chunks=total_chunks,
        file_header_size=file_header_size,
        chunk_header_size=chunk_header_size,
    )


def _copy_exact(source: BinaryIO, destination: BinaryIO, byte_count: int) -> None:
    remaining = byte_count
    while remaining:
        chunk = source.read(min(_COPY_BUFFER_SIZE, remaining))
        if not chunk:
            raise SparseImageError('Sparse RAW chunk is truncated')
        destination.write(chunk)
        remaining -= len(chunk)


def overlay_sparse_image(source_path: str | Path, destination: BinaryIO) -> SparseHeader:
    """Write allocated chunks from one sparse image into a seekable raw output."""
    source = Path(source_path)
    with source.open('rb') as stream:
        header = read_sparse_header(stream)
        current_block = 0
        for _index in range(header.total_chunks):
            raw_chunk_header = stream.read(header.chunk_header_size)
            if len(raw_chunk_header) != header.chunk_header_size:
                raise SparseImageError(f'Sparse chunk header is truncated in {source}')
            chunk_type, _reserved, chunk_blocks, total_size = _CHUNK.unpack(raw_chunk_header[:CHUNK_HEADER_SIZE])
            if chunk_blocks < 0:
                raise SparseImageError('Sparse chunk has an invalid block count')
            data_size = total_size - header.chunk_header_size
            if data_size < 0:
                raise SparseImageError('Sparse chunk total size is smaller than its header')
            output_offset = current_block * header.block_size
            if chunk_type == CHUNK_TYPE_RAW:
                expected = chunk_blocks * header.block_size
                if data_size != expected:
                    raise SparseImageError(
                        f'Sparse RAW chunk size mismatch in {source}: {data_size}, expected {expected}'
                    )
                destination.seek(output_offset)
                _copy_exact(stream, destination, expected)
            elif chunk_type == CHUNK_TYPE_FILL:
                if data_size != 4:
                    raise SparseImageError('Sparse FILL chunk must contain exactly four bytes')
                pattern = stream.read(4)
                if len(pattern) != 4:
                    raise SparseImageError('Sparse FILL pattern is truncated')
                destination.seek(output_offset)
                remaining = chunk_blocks * header.block_size
                repeated = pattern * min(262144, max(1, _COPY_BUFFER_SIZE // 4))
                while remaining:
                    block = repeated[:min(len(repeated), remaining)]
                    destination.write(block)
                    remaining -= len(block)
            elif chunk_type == CHUNK_TYPE_DONT_CARE:
                if data_size:
                    stream.seek(data_size, os.SEEK_CUR)
            elif chunk_type == CHUNK_TYPE_CRC32:
                if data_size != 4:
                    raise SparseImageError('Sparse CRC32 chunk must contain exactly four bytes')
                if len(stream.read(4)) != 4:
                    raise SparseImageError('Sparse CRC32 value is truncated')
            else:
                raise SparseImageError(f'Unsupported sparse chunk type: 0x{chunk_type:04x}')
            current_block += chunk_blocks
        if current_block != header.total_blocks:
            raise SparseImageError(
                f'Sparse block count mismatch in {source}: {current_block}, expected {header.total_blocks}'
            )
        return header


def merge_sparse_overlays(
    source_paths: Iterable[str | Path],
    output_path: str | Path,
    *,
    progress_callback: Callable[[int], None] | None = None,
) -> Path:
    sources = tuple(Path(path) for path in source_paths)
    if not sources:
        raise ValueError('At least one sparse image is required')
    headers: list[SparseHeader] = []
    for source in sources:
        with source.open('rb') as stream:
            headers.append(read_sparse_header(stream))
    block_sizes = {header.block_size for header in headers}
    if len(block_sizes) != 1:
        raise SparseImageError('Sparse parts use different block sizes')
    final_size = max(header.total_blocks for header in headers) * headers[0].block_size
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w+b',
            prefix=f'.{output.name}.',
            suffix='.part',
            dir=output.parent,
            delete=False,
        ) as destination:
            temporary_path = Path(destination.name)
            destination.truncate(final_size)
            for index, source in enumerate(sources, start=1):
                overlay_sparse_image(source, destination)
                if progress_callback is not None:
                    progress_callback(int(index * 100 / len(sources)))
            destination.flush()
            os.fsync(destination.fileno())
        temporary_path.replace(output)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    if output.stat().st_size != final_size:
        raise RuntimeError(f'Merged sparse output has an unexpected size: {output}')
    if progress_callback is not None:
        progress_callback(100)
    return output


def _write_sparse_piece(
    output_path: Path,
    source: BinaryIO,
    *,
    block_size: int,
    start_block: int,
    raw_blocks: int,
    total_blocks: int,
) -> None:
    if raw_blocks <= 0:
        raise ValueError('Sparse piece must contain at least one RAW block')
    chunk_count = 1 + int(start_block > 0)
    header = _HEADER.pack(
        SPARSE_HEADER_MAGIC,
        SPARSE_MAJOR_VERSION,
        0,
        SPARSE_HEADER_SIZE,
        CHUNK_HEADER_SIZE,
        block_size,
        total_blocks,
        chunk_count,
        0,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('wb') as destination:
        destination.write(header)
        if start_block:
            destination.write(_CHUNK.pack(CHUNK_TYPE_DONT_CARE, 0, start_block, CHUNK_HEADER_SIZE))
        raw_size = raw_blocks * block_size
        destination.write(_CHUNK.pack(CHUNK_TYPE_RAW, 0, raw_blocks, CHUNK_HEADER_SIZE + raw_size))
        _copy_exact(source, destination, raw_size)
        destination.flush()
        os.fsync(destination.fileno())


def split_raw_image_to_sparse_parts(
    source_path: str | Path,
    output_directory: str | Path,
    *,
    part_count: int = 15,
    block_size: int = 4096,
    suffix_format: str = '.%03d',
    keep_existing: bool = False,
    progress_callback: Callable[[int], None] | None = None,
) -> SparseSplitResult:
    source = Path(source_path)
    output_dir = Path(output_directory)
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f'Raw image was not found or is empty: {source}')
    if is_sparse_image(source):
        raise ValueError('Split Super requires a raw image, not an Android sparse image')
    if part_count < 2:
        raise ValueError('Part count must be at least 2')
    if block_size <= 0 or block_size % 4:
        raise ValueError('Block size must be a positive multiple of 4')
    source_size = source.stat().st_size
    if source_size % block_size:
        raise ValueError(f'Image size {source_size} is not aligned to block size {block_size}')
    total_blocks = source_size // block_size
    blocks_per_part = math.ceil(total_blocks / part_count)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not keep_existing:
        pattern = re.compile(rf'^{re.escape(source.name)}\.\d+$')
        for existing in output_dir.iterdir():
            if existing.is_file() and pattern.match(existing.name):
                existing.unlink()
    output_paths: list[Path] = []
    try:
        with source.open('rb') as input_stream:
            start_block = 0
            index = 0
            while start_block < total_blocks:
                raw_blocks = min(blocks_per_part, total_blocks - start_block)
                try:
                    suffix = suffix_format % index
                except Exception as exc:
                    raise ValueError(f'Invalid suffix format: {suffix_format!r}') from exc
                output_path = output_dir / f'{source.name}{suffix}'
                if output_path.exists():
                    raise FileExistsError(f'Sparse part already exists: {output_path}')
                _write_sparse_piece(
                    output_path,
                    input_stream,
                    block_size=block_size,
                    start_block=start_block,
                    raw_blocks=raw_blocks,
                    total_blocks=start_block + raw_blocks,
                )
                output_paths.append(output_path)
                start_block += raw_blocks
                index += 1
                if progress_callback is not None:
                    progress_callback(int(start_block * 100 / total_blocks))
    except Exception:
        for path in output_paths:
            path.unlink(missing_ok=True)
        raise
    if progress_callback is not None:
        progress_callback(100)
    return SparseSplitResult(
        source_path=source,
        output_paths=tuple(output_paths),
        block_size=block_size,
        total_blocks=total_blocks,
    )


__all__ = [
    'CHUNK_TYPE_CRC32',
    'CHUNK_TYPE_DONT_CARE',
    'CHUNK_TYPE_FILL',
    'CHUNK_TYPE_RAW',
    'SPARSE_HEADER_MAGIC',
    'SparseHeader',
    'SparseImageError',
    'SparseSplitResult',
    'is_sparse_image',
    'merge_sparse_overlays',
    'overlay_sparse_image',
    'parse_size_suffix',
    'read_sparse_header',
    'split_raw_image_to_sparse_parts',
]
