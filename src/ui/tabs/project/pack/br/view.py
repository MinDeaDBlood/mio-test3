from __future__ import annotations

from dataclasses import dataclass

from src.ui.common.technical_choices import technical_label
from src.ui.localization import LocalizationCatalog


@dataclass(frozen=True)
class PackViewSpec:
    output_value: str


SPEC = PackViewSpec(output_value="br")
FORMAT = SPEC.output_value


def get_output_value() -> str:
    return SPEC.output_value


def get_display_name(texts: LocalizationCatalog) -> str:
    return technical_label(texts, SPEC.output_value)
