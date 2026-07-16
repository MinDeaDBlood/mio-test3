from __future__ import annotations

from importlib import import_module

__all__ = ['not_none']

_EXPORTS = {'not_none': ('src.logic.common.service', 'not_none')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
