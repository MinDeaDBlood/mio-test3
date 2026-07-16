from __future__ import annotations

from importlib import import_module

__all__ = ['trim_trailing_zeros']

_EXPORTS = {'trim_trailing_zeros': ('src.logic.tools.trim_raw_image.service', 'trim_trailing_zeros')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
