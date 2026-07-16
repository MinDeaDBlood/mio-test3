from __future__ import annotations

from dataclasses import dataclass

from src.logic.common.service_output import ServiceOutput


@dataclass(frozen=True)
class DtboRuntimeContext:
    work_path: str
    output_path: str
    output: ServiceOutput


def build_dtbo_runtime_context(
    *,
    work_path: str,
    output_path: str,
    output: ServiceOutput,
) -> DtboRuntimeContext:
    return DtboRuntimeContext(
        work_path=str(work_path),
        output_path=str(output_path),
        output=output,
    )


__all__ = ["DtboRuntimeContext", "build_dtbo_runtime_context"]
