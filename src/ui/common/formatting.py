from __future__ import annotations

from enum import Enum

_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")


def enum_value(value: object) -> object:
    """Return the stored value of an Enum, otherwise return the object unchanged."""
    return value.value if isinstance(value, Enum) else value


def format_bytes(value: int | float) -> str:
    if not isinstance(value, (int, float)):
        raise TypeError(f"Byte size must be numeric, got {type(value).__name__}")
    amount = float(value)
    for unit in _UNITS:
        if abs(amount) < 1024.0:
            return f"{amount:.2f}{unit}"
        amount /= 1024.0
    return f"{amount:.2f}EB"


__all__ = ["enum_value", "format_bytes"]
