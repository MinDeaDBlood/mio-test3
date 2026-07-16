from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PackViewSpec:
    output_value: str
    display_name: str


SPEC = PackViewSpec(output_value="dat", display_name="dat")
FORMAT = SPEC.output_value


def get_output_value() -> str:
    return SPEC.output_value


def get_display_name() -> str:
    return SPEC.display_name
