from __future__ import annotations

from importlib import import_module

__all__ = ['is_plugin_installed']

_EXPORTS = {'is_plugin_installed': ('src.logic.plugins.sandbox.service', 'is_plugin_installed')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
