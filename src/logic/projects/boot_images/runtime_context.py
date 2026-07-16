from __future__ import annotations

from dataclasses import dataclass

from src.logic.common.service_output import ServiceOutput


@dataclass(frozen=True)
class BootImageRuntimeContext:
    input_path: str
    work_path: str
    output_path: str
    tool_bin: str
    magisk_not_decompress: str
    boot_skip_ramdisk: str
    output: ServiceOutput


def build_runtime_context(
    *,
    input_path: str,
    work_path: str,
    output_path: str,
    tool_bin: str,
    magisk_not_decompress: str,
    boot_skip_ramdisk: str,
    output: ServiceOutput,
) -> BootImageRuntimeContext:
    return BootImageRuntimeContext(
        input_path=str(input_path),
        work_path=str(work_path),
        output_path=str(output_path),
        tool_bin=str(tool_bin),
        magisk_not_decompress=str(magisk_not_decompress),
        boot_skip_ramdisk=str(boot_skip_ramdisk),
        output=output,
    )


__all__ = ["BootImageRuntimeContext", "build_runtime_context"]
