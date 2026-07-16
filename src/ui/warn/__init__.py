from __future__ import annotations

from importlib import import_module

__all__ = ['warn_win', 'ask_win', 'info_win']


def __getattr__(name: str):
    if name in {'warn_win', 'ask_win', 'info_win'}:
        module = import_module('src.ui.warn.dialogs')
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
