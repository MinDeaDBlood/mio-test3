from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.ui.common.editor.window import PythonEditor

__all__ = ["PythonEditor"]


def __getattr__(name: str):
    if name == "PythonEditor":
        value = import_module("src.ui.common.editor.window").PythonEditor
        globals()[name] = value
        return value
    raise AttributeError(name)
