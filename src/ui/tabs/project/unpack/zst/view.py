from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class UnpackViewSpec:
    option_value: str
    display_name: str


SPEC = UnpackViewSpec(option_value="zst", display_name="zst")
FORMAT = SPEC.option_value


def get_option_value() -> str:
    return SPEC.option_value


def get_display_name() -> str:
    return SPEC.display_name
