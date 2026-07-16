from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class Ext4SizeMode(str, Enum):
    AUTO = 'auto'
    FIXED = 'fixed'


@dataclass(frozen=True)
class PackPartitionRequest:
    chosen_parts: list[str]
    patch_vbmeta: bool
    remove_source_files: bool
    ext4_packer: str
    ext4_size_mode: Ext4SizeMode
    output_format: str
    erofs_compress_format: str
    erofs_level: int
    brotli_level: int
    utc: int
    origin_fs: str
    modify_fs: str
    fs_convert: bool
    erofs_old_kernel: bool
    custom_size: Mapping[str, int | str]


__all__ = ['Ext4SizeMode', 'PackPartitionRequest']
