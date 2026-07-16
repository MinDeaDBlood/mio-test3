from __future__ import annotations

from dataclasses import dataclass

from src.logic.common.service_output import ServiceOutput


@dataclass(frozen=True)
class ConvertRuntimeContext:
    work_path: str
    output_path: str
    output: ServiceOutput


def build_convert_runtime_context(
    *,
    work_path: str,
    output_path: str,
    output: ServiceOutput,
) -> ConvertRuntimeContext:
    return ConvertRuntimeContext(
        work_path=str(work_path),
        output_path=str(output_path),
        output=output,
    )


__all__ = ["ConvertRuntimeContext", "build_convert_runtime_context"]
