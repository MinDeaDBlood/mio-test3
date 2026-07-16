from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import re
from numbers import Real

from src.core.byte_size import format_bytes
from src.logic.common.messages import message
from src.logic.common.service_output import ServiceOutput, build_service_output


_MIN_EXT4_SIZE = 2 * 1024 * 1024
_LEGACY_SMALL_EXT4_SIZE = 1024 * 1024
_EXT4_BLOCK_SIZE = 4096
_LARGE_IMAGE_THRESHOLD = 100 * 1024 * 1024
_LARGE_IMAGE_PADDING = 16 * 1024 * 1024


@dataclass(frozen=True)
class Ext4SizeFit:
    requested_size: int
    recommended_size: int

    @property
    def fits(self) -> bool:
        return self.requested_size <= 0 or self.requested_size >= self.recommended_size

    @property
    def missing_bytes(self) -> int:
        return max(0, self.recommended_size - self.requested_size)


def check_ext4_size_fit(directory: str, requested_size: int | str | None) -> Ext4SizeFit:
    """Return whether a fixed EXT4 image size is likely large enough.

    ``requested_size`` is the explicit/original size selected by the UI.  Auto
    size uses ``0`` and remains handled by the filesystem packer, which can also
    update dynamic_partitions_op_list when needed.  This helper is deliberately
    advisory: callers should use it to explain fixed-size failures, not to silently
    resize a partition after the user selected Same as original/custom size.
    """
    fixed_size = _coerce_size_value(requested_size)
    if fixed_size <= 0:
        return Ext4SizeFit(requested_size=0, recommended_size=0)
    recommended = normalize_ext_image_size(estimate_directory_image_size(directory))
    return Ext4SizeFit(requested_size=fixed_size, recommended_size=recommended)


def estimate_directory_image_size(directory: str) -> Real:
    """Return the legacy image-size estimate for a partition directory.

    The formula intentionally preserves the old packer heuristic: add file sizes,
    add sparse/metadata overhead, and keep the legacy padding for big images.  Keeping
    it here makes the heuristic explicit and keeps filesystem packers focused on
    command orchestration.
    """
    size: Real = 0
    for root, _, files in os.walk(directory):
        for name in files:
            try:
                file_path = os.path.join(root, name)
                if not os.path.isfile(file_path):
                    size += len(name)
                size += os.path.getsize(file_path)
            except OSError:
                logging.exception(f'Getsize {name}')
                size += 1
    size += (size / 16384) * 256
    if size > _LARGE_IMAGE_THRESHOLD:
        size += _LARGE_IMAGE_PADDING
    return size


def normalize_ext_image_size(size: Real, divisor: int = 1) -> int:
    """Normalize the estimated size using the legacy ext-image block rules."""
    if size <= _MIN_EXT4_SIZE:
        normalized = _MIN_EXT4_SIZE
    elif size <= _LEGACY_SMALL_EXT4_SIZE:
        # Kept for behavioral compatibility with the historical branch order.
        normalized = _LEGACY_SMALL_EXT4_SIZE
    else:
        normalized = int(size)
        if normalized % _EXT4_BLOCK_SIZE:
            normalized += _EXT4_BLOCK_SIZE - normalized % _EXT4_BLOCK_SIZE
    return int(normalized / divisor)


def format_image_size_estimate(size: Real) -> str:
    return format_bytes(size)


def update_dynamic_partition_size(part_name: str, size: int, file: str | None, *, output: ServiceOutput | None = None) -> None:
    """Update resize lines for a partition in dynamic_partitions_op_list."""
    if not file:
        return
    output = output or build_service_output()
    if os.access(file, os.F_OK):
        output.log(message('size_detected', 'Detected size for {item}: {size}', item=part_name, size=size))
        with open(file, 'r', encoding='utf-8') as handle:
            content = handle.read()
        with open(file, 'w', encoding='utf-8', newline='\n') as handle:
            content = re.sub(rf'resize {part_name} \d+', f'resize {part_name} {size}', content)
            content = re.sub(rf'resize {part_name}_a \d+', f'resize {part_name}_a {size}', content)
            content = re.sub(rf'# Grow partition {part_name} from 0 to \d+', f'# Grow partition {part_name} from 0 to {size}', content)
            content = re.sub(rf'# Grow partition {part_name}_a from 0 to \d+', f'# Grow partition {part_name}_a from 0 to {size}', content)
            handle.write(content)


def resolve_partition_image_size(
    directory: str,
    *,
    divisor: int = 1,
    mode: int = 2,
    list_file: str | None = None,
    output: ServiceOutput | None = None,
) -> int | Real:
    """Resolve the legacy GetFolderSize result without coupling packers to os.walk.

    mode=1 returns the raw legacy estimate; other modes return a normalized size.
    mode=3 additionally updates dynamic_partitions_op_list through the helper above.
    """
    size = estimate_directory_image_size(directory)
    if mode == 1:
        return size
    partition_name = os.path.basename(directory)
    normalized = normalize_ext_image_size(size, divisor=divisor)
    output = output or build_service_output()
    output.log(f'{partition_name} Size : {format_bytes(size)}')
    if mode == 3:
        update_dynamic_partition_size(partition_name, normalized, list_file, output=output)
    return normalized


def resolve_configured_ext4_size(
    work: str,
    partition_name: str,
    custom_size: int | str | None = None,
    *,
    prefer_dynamic_resize: bool = False,
) -> int:
    """Resolve the ext4 image size requested by the partition-pack UI.

    Size sources use an explicit precedence policy. A custom value is used first.
    When dynamic sizing is requested, dynamic_partitions_op_list is checked before
    the historical *_size.txt metadata file. A result of 0 explicitly selects
    automatic estimation by the filesystem packer.
    """
    size_value = _coerce_size_value(custom_size)
    if size_value or not prefer_dynamic_resize:
        return size_value
    op_list_size = read_dynamic_resize_size(work, partition_name)
    if op_list_size:
        return op_list_size
    return read_partition_size_file(work, partition_name)


def read_dynamic_resize_size(work: str, partition_name: str) -> int:
    """Return the largest resize value for partition/a/b variants."""
    list_file = os.path.join(work, 'dynamic_partitions_op_list')
    if not os.path.exists(list_file):
        return 0
    expected_names = {partition_name, f'{partition_name}_a', f'{partition_name}_b'}
    max_size = 0
    with open(list_file, 'r', encoding='utf-8') as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) < 3 or parts[0] != 'resize' or parts[1] not in expected_names:
                continue
            try:
                max_size = max(max_size, int(parts[2]))
            except ValueError:
                continue
    return max_size


def read_partition_size_file(work: str, partition_name: str) -> int:
    size_file = os.path.join(work, 'config', f'{partition_name}_size.txt')
    if not os.path.exists(size_file):
        return 0
    try:
        with open(size_file, 'r', encoding='utf-8') as handle:
            return int(handle.read().strip())
    except ValueError:
        return 0


def _coerce_size_value(value: int | str | None) -> int:
    if value in (None, ''):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    'Ext4SizeFit',
    'check_ext4_size_fit',
    'estimate_directory_image_size',
    'format_image_size_estimate',
    'normalize_ext_image_size',
    'read_dynamic_resize_size',
    'read_partition_size_file',
    'resolve_configured_ext4_size',
    'resolve_partition_image_size',
    'update_dynamic_partition_size',
]
