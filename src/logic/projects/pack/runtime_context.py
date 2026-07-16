from __future__ import annotations

from dataclasses import dataclass

from src.logic.common.service_output import ServiceOutput


@dataclass(frozen=True)
class PackPartitionRuntimeContext:
    input_path: str
    work_path: str
    output_path: str
    project_selected: bool
    context_patch_enabled: bool
    context_rule_file: str
    tool_bin: str
    magisk_not_decompress: str
    boot_skip_ramdisk: str
    output: ServiceOutput


__all__ = ["PackPartitionRuntimeContext"]
