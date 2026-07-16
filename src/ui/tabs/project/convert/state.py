from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConvertViewState:
    input_formats: tuple[str, ...]
    output_formats: tuple[str, ...]


__all__ = ["ConvertViewState"]
