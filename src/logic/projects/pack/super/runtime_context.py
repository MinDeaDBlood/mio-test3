from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PackSuperRuntimeContext:
    work_path: str
    output_path: str


def build_pack_super_runtime_context(
    *, work_path: str, output_path: str
) -> PackSuperRuntimeContext:
    return PackSuperRuntimeContext(
        work_path=str(work_path), output_path=str(output_path)
    )


__all__ = ["PackSuperRuntimeContext", "build_pack_super_runtime_context"]
