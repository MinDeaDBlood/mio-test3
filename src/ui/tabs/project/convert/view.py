from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.ui.tabs.project.convert.frame import FormatConversion

__all__ = ["FormatConversion"]


def __getattr__(name: str):
    if name != "FormatConversion":
        raise AttributeError(name)
    value = getattr(import_module("src.ui.tabs.project.convert.frame"), name)
    globals()[name] = value
    return value
