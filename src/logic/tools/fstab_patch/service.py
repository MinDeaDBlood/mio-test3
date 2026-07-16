from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, TypeAlias

from src.core.avb_disabler import AvbPatchResult
from src.core.encryption_disabler import EncryptionPatchResult

FstabPatchResult: TypeAlias = AvbPatchResult | EncryptionPatchResult


@dataclass(frozen=True)
class FstabPartition:
    name: str
    fs_type: str
    paths: tuple[str, ...]


def _read_parts_info(work_path: str, json_edit_cls) -> dict[str, str]:
    parts_info_path = os.path.join(work_path, 'config', 'parts_info')
    if not os.path.isfile(parts_info_path):
        return {}
    data = json_edit_cls(parts_info_path).read()
    return data if isinstance(data, dict) else {}


def load_fstab_partitions(work_path: str, *, json_edit_cls) -> tuple[FstabPartition, ...]:
    parts_info = _read_parts_info(work_path, json_edit_cls)
    result: list[FstabPartition] = []
    for item_name in sorted(os.listdir(work_path)):
        item_path = os.path.join(work_path, item_name)
        if not os.path.isdir(item_path):
            continue
        paths: list[str] = []
        for root, _, files in os.walk(item_path):
            for file_name in files:
                if 'fstab' in file_name.lower():
                    paths.append(os.path.join(root, file_name))
        if paths:
            result.append(
                FstabPartition(
                    name=item_name,
                    fs_type=str(parts_info.get(item_name, 'unknown')),
                    paths=tuple(paths),
                )
            )
    return tuple(result)


def patch_selected_partitions(
    partitions: tuple[FstabPartition, ...] | list[FstabPartition],
    selected_partitions: tuple[str, ...] | list[str],
    *,
    patch_file: Callable[[str], FstabPatchResult],
) -> int:
    by_name = {partition.name: partition for partition in partitions}
    processed_count = 0
    for partition_name in selected_partitions:
        partition = by_name.get(partition_name)
        if partition is None:
            continue
        results = [patch_file(path) for path in partition.paths]
        if any(result.modified for result in results):
            processed_count += 1
    return processed_count


__all__ = ['FstabPartition', 'FstabPatchResult', 'load_fstab_partitions', 'patch_selected_partitions']
