from __future__ import annotations

from dataclasses import dataclass

from src.logic.common.service_output import ServiceOutput


@dataclass(frozen=True)
class UnpackWorkflowRuntimeContext:
    input_path: str
    work_path: str
    output_path: str
    project_selected: bool
    tool_bin: str
    magisk_not_decompress: str
    boot_skip_ramdisk: str
    output: ServiceOutput

    def project_exists(self) -> bool:
        return bool(self.project_selected)


def build_workflow_runtime_context(
    *,
    input_path: str,
    work_path: str,
    output_path: str,
    project_selected: bool,
    tool_bin: str,
    magisk_not_decompress: str,
    boot_skip_ramdisk: str,
    output: ServiceOutput,
) -> UnpackWorkflowRuntimeContext:
    if output is None:
        raise ValueError("Unpack workflow runtime requires an output port.")
    return UnpackWorkflowRuntimeContext(
        input_path=str(input_path),
        work_path=str(work_path),
        output_path=str(output_path),
        project_selected=bool(project_selected),
        tool_bin=str(tool_bin),
        magisk_not_decompress=str(magisk_not_decompress),
        boot_skip_ramdisk=str(boot_skip_ramdisk),
        output=output,
    )


__all__ = ["UnpackWorkflowRuntimeContext", "build_workflow_runtime_context"]
