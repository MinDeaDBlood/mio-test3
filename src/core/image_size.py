from __future__ import annotations

import os
import struct
from pathlib import Path

ANDROID_SPARSE_HEADER_MAGIC = 0xED26FF3A
_ANDROID_SPARSE_HEADER_FORMAT = '<I4H4I'
_ANDROID_SPARSE_HEADER_SIZE = struct.calcsize(_ANDROID_SPARSE_HEADER_FORMAT)


def android_sparse_logical_size(path: str | os.PathLike[str]) -> int | None:
    """Return the unsparsed logical size for an Android sparse image.

    Android sparse files store only populated chunks on disk, so ``os.path.getsize``
    is the container size, not the partition/device size that tools such as
    ``lpmake`` must receive.  ``None`` means the file is not a valid Android
    sparse image or the header cannot be read.
    """
    try:
        with open(path, 'rb') as image_file:
            header = image_file.read(_ANDROID_SPARSE_HEADER_SIZE)
    except OSError:
        return None
    if len(header) < _ANDROID_SPARSE_HEADER_SIZE:
        return None
    try:
        (
            magic,
            major_version,
            _minor_version,
            file_hdr_sz,
            _chunk_hdr_sz,
            block_size,
            total_blocks,
            _total_chunks,
            _checksum,
        ) = struct.unpack(_ANDROID_SPARSE_HEADER_FORMAT, header)
    except struct.error:
        return None
    if magic != ANDROID_SPARSE_HEADER_MAGIC:
        return None
    if major_version != 1 or file_hdr_sz < _ANDROID_SPARSE_HEADER_SIZE:
        return None
    if block_size <= 0 or total_blocks < 0:
        return None
    return int(block_size) * int(total_blocks)


def image_logical_size(path: str | os.PathLike[str]) -> int:
    """Return the logical image size, expanding Android sparse headers when needed."""
    sparse_size = android_sparse_logical_size(path)
    if sparse_size is not None:
        return sparse_size
    return Path(path).stat().st_size


__all__ = ['ANDROID_SPARSE_HEADER_MAGIC', 'android_sparse_logical_size', 'image_logical_size']
