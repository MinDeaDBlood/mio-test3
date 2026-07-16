from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from chlorophyll import CodeView

__all__ = ["CodeView"]


def __getattr__(name: str):
    if name == "CodeView":
        value = import_module("chlorophyll").CodeView
        globals()[name] = value
        return value
    raise AttributeError(name)
