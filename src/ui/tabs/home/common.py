from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.ui.common.widgets.toggled_frame import ToggledFrame
    from src.ui.common.windowing import CustomControls, Toplevel, warn_win

__all__ = ["warn_win", "Toplevel", "CustomControls", "ToggledFrame"]

_LAZY_EXPORTS = {
    "ToggledFrame": ("src.ui.common.widgets.toggled_frame", "ToggledFrame"),
    "CustomControls": ("src.ui.common.windowing", "CustomControls"),
    "Toplevel": ("src.ui.common.windowing", "Toplevel"),
    "warn_win": ("src.ui.common.windowing", "warn_win"),
}


def __getattr__(name: str):
    try:
        module_name, attr_name = _LAZY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
