from __future__ import annotations

from src.core.encryption_disabler import process_fstab_for_encryption
from src.logic.tools.fstab_patch.service import FstabPartition, load_fstab_partitions, patch_selected_partitions as patch_partitions


def scan_project_for_fstab_partitions(work_path: str, *, json_edit_cls) -> tuple[FstabPartition, ...]:
    return load_fstab_partitions(work_path, json_edit_cls=json_edit_cls)


def patch_selected_partitions(
    partitions: tuple[FstabPartition, ...] | list[FstabPartition],
    selected_partitions: tuple[str, ...] | list[str],
) -> int:
    return patch_partitions(partitions, selected_partitions, patch_file=process_fstab_for_encryption)


__all__ = ['FstabPartition', 'patch_selected_partitions', 'scan_project_for_fstab_partitions']
