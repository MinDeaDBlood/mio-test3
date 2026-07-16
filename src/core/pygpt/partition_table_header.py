from __future__ import annotations

import logging
import math
import struct
import zlib
from dataclasses import dataclass
from uuid import UUID

from .gpt_file import GPTFile
from .partition_table_entry import PartitionTableEntry

logger = logging.getLogger(__name__)

GPT_SIGNATURE = b'EFI PART'
GPT_HEADER_MIN_SIZE = 92
GPT_DEFAULT_ENTRY_SIZE = 128
_HEADER_STRUCT = struct.Struct('<8sIIIIQQQQ16sQIII')


class GPTHeaderError(ValueError):
    pass


@dataclass(frozen=True)
class HeaderMetadata:
    current_lba: int
    backup_lba: int
    first_usable_lba: int
    last_usable_lba: int
    disk_uuid: UUID
    partition_start_lba: int
    entry_count: int
    entry_size: int
    entry_crc32: int
    is_backup: bool


class PartitionTableHeader:
    """Validated GPT header and partition entry table."""

    def __init__(self, gptfile: GPTFile, little_endian: bool = True) -> None:
        if not little_endian:
            raise NotImplementedError('Big endian GPT is not supported')
        self._gptfile = gptfile
        self._partitions: list[PartitionTableEntry] = []
        self._metadata = self._find_header()
        self._load_entries()

    @property
    def metadata(self) -> HeaderMetadata:
        return self._metadata

    def valid_entries(self):
        return (entry for entry in self._partitions if not entry.is_unused)

    def _parse_header(self, raw_sector: bytes, *, is_backup: bool) -> HeaderMetadata:
        if len(raw_sector) < GPT_HEADER_MIN_SIZE:
            raise GPTHeaderError('GPT header sector is too small')
        unpacked = _HEADER_STRUCT.unpack(raw_sector[:_HEADER_STRUCT.size])
        (
            signature,
            revision,
            header_size,
            header_crc32,
            reserved,
            current_lba,
            backup_lba,
            first_usable_lba,
            last_usable_lba,
            disk_uuid_raw,
            partition_start_lba,
            entry_count,
            entry_size,
            entry_crc32,
        ) = unpacked
        if signature != GPT_SIGNATURE:
            raise GPTHeaderError('GPT signature was not found')
        if revision >> 16 != 1:
            raise GPTHeaderError(f'Unsupported GPT major revision: {revision >> 16}')
        if reserved != 0:
            logger.warning('GPT reserved header field is not zero')
        if header_size < GPT_HEADER_MIN_SIZE or header_size > len(raw_sector):
            raise GPTHeaderError(f'Invalid GPT header size: {header_size}')
        header_for_crc = bytearray(raw_sector[:header_size])
        header_for_crc[16:20] = b'\x00\x00\x00\x00'
        calculated_crc = zlib.crc32(header_for_crc) & 0xFFFFFFFF
        if calculated_crc != header_crc32:
            raise GPTHeaderError(
                f'GPT header CRC mismatch: expected {header_crc32:08x}, calculated {calculated_crc:08x}'
            )
        if entry_count <= 0:
            raise GPTHeaderError('GPT entry count must be positive')
        if entry_size < GPT_DEFAULT_ENTRY_SIZE or entry_size % 8 != 0:
            raise GPTHeaderError(f'Unsupported GPT entry size: {entry_size}')
        if first_usable_lba > last_usable_lba:
            raise GPTHeaderError('GPT usable sector range is invalid')
        return HeaderMetadata(
            current_lba=current_lba,
            backup_lba=backup_lba,
            first_usable_lba=first_usable_lba,
            last_usable_lba=last_usable_lba,
            disk_uuid=UUID(bytes_le=disk_uuid_raw),
            partition_start_lba=partition_start_lba,
            entry_count=entry_count,
            entry_size=entry_size,
            entry_crc32=entry_crc32,
            is_backup=is_backup,
        )

    def _find_header(self) -> HeaderMetadata:
        errors: list[str] = []
        for lba, is_backup in ((1, False), (-1, True)):
            try:
                return self._parse_header(self._gptfile.read_blocks(lba, 1), is_backup=is_backup)
            except (GPTHeaderError, ValueError, EOFError) as exc:
                errors.append(f'{"backup" if is_backup else "primary"}: {exc}')
        raise GPTHeaderError('Could not load GPT header. ' + '; '.join(errors))

    def _load_entries(self) -> None:
        metadata = self._metadata
        byte_count = metadata.entry_count * metadata.entry_size
        block_count = math.ceil(byte_count / self._gptfile.sector_size)
        raw_padded = self._gptfile.read_blocks(metadata.partition_start_lba, block_count)
        raw_entries = raw_padded[:byte_count]
        calculated_crc = zlib.crc32(raw_entries) & 0xFFFFFFFF
        if calculated_crc != metadata.entry_crc32:
            raise GPTHeaderError(
                f'GPT entry table CRC mismatch: expected {metadata.entry_crc32:08x}, calculated {calculated_crc:08x}'
            )
        for index in range(metadata.entry_count):
            start = index * metadata.entry_size
            entry_raw = raw_entries[start:start + metadata.entry_size]
            self._partitions.append(PartitionTableEntry.from_bytes(entry_raw))


__all__ = [
    'GPT_DEFAULT_ENTRY_SIZE',
    'GPT_HEADER_MIN_SIZE',
    'GPT_SIGNATURE',
    'GPTHeaderError',
    'HeaderMetadata',
    'PartitionTableHeader',
]
