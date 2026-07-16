from __future__ import annotations

import io
import os
from functools import partial
from typing import Any, BinaryIO

from .const import SQUASHFS_MAGIC, Compression
from .structure import Superblock


MAGIC_BYTES = SQUASHFS_MAGIC.to_bytes(4, 'little')


def check_super(sblk):
    if sblk.s_magic != SQUASHFS_MAGIC or sblk.s_major != 4 or sblk.s_minor != 0:
        return False
    if not min(Compression) <= sblk.compression <= max(Compression):
        return False
    return True


def _find_superblocks(stream: BinaryIO, size: int = 1024**2):
    stream.seek(0)
    indexes = set()
    result = []
    prev_block = b''
    for count, next_block in enumerate(iter(partial(stream.read, size), b'')):
        block = prev_block + next_block
        index = block.find(MAGIC_BYTES)
        if index != -1:
            indexes.add(index + (count * size) - len(prev_block))
        prev_block = next_block[-(len(MAGIC_BYTES) - 1) :]
    for index in sorted(indexes):
        stream.seek(index)
        sblk = Superblock.from_fd(stream)
        if check_super(sblk):
            result.append(dict(sblk, offset=index))
    return result


def find_superblocks(file_or_bytes: Any, size: int = 1024**2):
    """Find SquashFS superblocks in a binary stream, path, or bytes value.

    Accepted input types are explicit. The function does not retry the same input
    using a different interpretation after an exception.
    """
    if hasattr(file_or_bytes, 'read') and hasattr(file_or_bytes, 'seek'):
        return _find_superblocks(file_or_bytes, size)
    if isinstance(file_or_bytes, (str, os.PathLike)):
        with open(file_or_bytes, 'rb') as stream:
            return _find_superblocks(stream, size)
    if isinstance(file_or_bytes, (bytes, bytearray, memoryview)):
        return _find_superblocks(io.BytesIO(bytes(file_or_bytes)), size)
    raise TypeError(
        'file_or_bytes must be a seekable binary stream, filesystem path, or bytes-like value.'
    )
