from __future__ import annotations

from dataclasses import dataclass

from src.ui.common.technical_choices import technical_label
from src.ui.localization import LocalizationCatalog


@dataclass(frozen=True)
class UnpackViewSpec:
    option_value: str


SPEC = UnpackViewSpec(option_value="update.app")
FORMAT = SPEC.option_value


def get_option_value() -> str:
    return SPEC.option_value


def get_display_name(texts: LocalizationCatalog) -> str:
    return technical_label(texts, SPEC.option_value)
