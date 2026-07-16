from __future__ import annotations

from importlib import import_module

__all__ = ['get_services']

_EXPORTS = {'get_services': ('src.logic.help.registry', 'get_services')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
