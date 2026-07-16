from __future__ import annotations

import logging
from pathlib import Path
from typing import BinaryIO, Iterator

logger = logging.getLogger(__name__)


class GPTFile:
    """Block oriented reader for a disk image."""

    def __init__(self, filename: str | Path, blocksz: int = 512) -> None:
        if blocksz <= 0:
            raise ValueError('Sector size must be positive')
        self._blocksz = int(blocksz)
        self._filename = Path(filename)
        self._nr_bytes = self._filename.stat().st_size
        if self._nr_bytes < self._blocksz:
            raise ValueError('The image is smaller than one sector')
        self._total_blocks = self._nr_bytes // self._blocksz
        self._file: BinaryIO = self._filename.open('rb')
        self._offset = 0
        logger.debug('GPT image %s contains %d sectors', self._filename, self._total_blocks)

    @property
    def filename(self) -> Path:
        return self._filename

    @property
    def sector_size(self) -> int:
        return self._blocksz

    @property
    def total_blocks(self) -> int:
        return self._total_blocks

    def read_blocks(self, lba_start: int, nr_blocks: int = 1) -> bytes:
        if nr_blocks < 0:
            raise ValueError('Number of sectors cannot be negative')
        start_block = self._total_blocks + lba_start if lba_start < 0 else lba_start
        if start_block < 0 or start_block > self._total_blocks:
            raise ValueError(f'Sector {lba_start} is outside the image')
        if start_block + nr_blocks > self._total_blocks:
            raise ValueError('Requested sector range is outside the image')
        byte_offset = start_block * self._blocksz
        if self._offset != byte_offset:
            self._file.seek(byte_offset)
            self._offset = byte_offset
        data = self._file.read(nr_blocks * self._blocksz)
        expected = nr_blocks * self._blocksz
        if len(data) != expected:
            raise EOFError(f'Expected {expected} bytes, received {len(data)}')
        self._offset += len(data)
        return data

    def read_bytes(self, byte_offset: int, length: int) -> bytes:
        if byte_offset < 0 or length < 0 or byte_offset + length > self._nr_bytes:
            raise ValueError('Requested byte range is outside the image')
        self._file.seek(byte_offset)
        self._offset = byte_offset
        data = self._file.read(length)
        if len(data) != length:
            raise EOFError(f'Expected {length} bytes, received {len(data)}')
        self._offset += len(data)
        return data

    def blocks_in_range(self, lba_start: int, nr_blocks: int) -> Iterator[bytes]:
        for index in range(nr_blocks):
            yield self.read_blocks(lba_start + index, 1)

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> 'GPTFile':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.close()
        return False
