from __future__ import annotations

from importlib import import_module

__all__ = ['get_plugin_setting']

_EXPORTS = {'get_plugin_setting': ('src.logic.settings.plugin_settings.service', 'get_plugin_setting')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
