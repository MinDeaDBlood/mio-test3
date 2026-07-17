from __future__ import annotations

from enum import Enum


def enum_value(value: object) -> object:
    """Return the stored value of an Enum, otherwise return the object unchanged."""

    return value.value if isinstance(value, Enum) else value


__all__ = ["enum_value"]
