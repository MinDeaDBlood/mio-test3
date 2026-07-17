from __future__ import annotations

from collections.abc import Sequence

from src.ui.common.technical_choices import technical_label
from src.ui.localization import LocalizationCatalog

_DISPLAY_UNITS = ("B", "KB", "MB", "GB", "TB", "PB", "EB")
_BINARY_DISPLAY_UNITS = ("B", "KiB", "MiB", "GiB", "TiB")


def _format_size(
    value: int | float,
    *,
    texts: LocalizationCatalog,
    units: Sequence[str],
    exact_byte_count: bool,
) -> str:
    if not isinstance(value, (int, float)):
        raise TypeError(f"Byte size must be numeric, got {type(value).__name__}")
    amount = float(value)
    unit = units[0]
    for unit in units:
        if abs(amount) < 1024.0 or unit == units[-1]:
            break
        amount /= 1024.0
    unit_label = technical_label(texts, unit)
    if exact_byte_count and unit == "B":
        return f"{int(value)} {unit_label}"
    return f"{amount:.2f} {unit_label}"


def format_localized_byte_size(
    value: int | float,
    *,
    texts: LocalizationCatalog,
) -> str:
    """Format a byte count with localized B, KB, MB and larger labels."""

    return _format_size(
        value,
        texts=texts,
        units=_DISPLAY_UNITS,
        exact_byte_count=False,
    )


def format_localized_binary_byte_size(
    value: int | float,
    *,
    texts: LocalizationCatalog,
) -> str:
    """Format a byte count with localized B, KiB, MiB, GiB and TiB labels."""

    return _format_size(
        value,
        texts=texts,
        units=_BINARY_DISPLAY_UNITS,
        exact_byte_count=True,
    )


__all__ = [
    "format_localized_binary_byte_size",
    "format_localized_byte_size",
]
