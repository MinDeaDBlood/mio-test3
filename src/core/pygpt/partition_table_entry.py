from __future__ import annotations

import struct
from dataclasses import dataclass
from uuid import UUID

from .partition_types import PartitionTypes

_ENTRY_STRUCT = struct.Struct('<16s16sQQQ72s')


@dataclass(frozen=True)
class PartitionTableEntry:
    partition_type: PartitionTypes | UUID
    partition_id: UUID
    first_block: int
    last_block: int
    attributes: int
    name: str

    @classmethod
    def from_bytes(cls, raw_entry: bytes) -> 'PartitionTableEntry':
        if len(raw_entry) < _ENTRY_STRUCT.size:
            raise ValueError(f'GPT entry is too small: {len(raw_entry)} bytes')
        type_raw, id_raw, first_lba, last_lba, attributes, name_raw = _ENTRY_STRUCT.unpack(
            raw_entry[:_ENTRY_STRUCT.size]
        )
        type_uuid = UUID(bytes_le=type_raw)
        partition_id = UUID(bytes_le=id_raw)
        try:
            partition_type: PartitionTypes | UUID = PartitionTypes(type_uuid)
        except ValueError:
            partition_type = type_uuid
        name = name_raw.decode('utf-16-le', errors='strict').rstrip('\x00')
        return cls(
            partition_type=partition_type,
            partition_id=partition_id,
            first_block=first_lba,
            last_block=last_lba,
            attributes=attributes,
            name=name,
        )

    @property
    def is_unused(self) -> bool:
        return self.partition_type == PartitionTypes.Unused

    @property
    def length(self) -> int:
        if self.is_unused:
            return 0
        if self.last_block < self.first_block:
            raise ValueError(f'GPT partition {self.name!r} has an invalid sector range')
        return self.last_block + 1 - self.first_block
