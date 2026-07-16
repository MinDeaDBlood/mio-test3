from __future__ import annotations

from pathlib import Path

from .gpt_file import GPTFile
from .partition_table_header import GPTHeaderError, PartitionTableHeader

GPTError = GPTHeaderError


class GPTReader:
    def __init__(self, filename: str | Path, sector_size: int = 512, little_endian: bool = True) -> None:
        self._filename = Path(filename)
        self._sector_size = sector_size
        self._file = GPTFile(self._filename, sector_size)
        try:
            self._partition_table = PartitionTableHeader(self._file, little_endian)
        except Exception:
            self._file.close()
            raise

    @property
    def partition_table(self) -> PartitionTableHeader:
        return self._partition_table

    @property
    def block_reader(self) -> GPTFile:
        return self._file

    @property
    def sector_size(self) -> int:
        return self._sector_size

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> 'GPTReader':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.close()
        return False


__all__ = ['GPTError', 'GPTReader']
