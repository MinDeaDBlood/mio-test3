from __future__ import annotations

from importlib import import_module

__all__ = ['list_plugins']

_EXPORTS = {'list_plugins': ('src.logic.plugins.discovery.service', 'list_plugins')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
