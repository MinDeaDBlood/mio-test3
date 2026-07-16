from __future__ import annotations

from importlib import import_module

__all__ = ['PluginInstallService', 'install_plugin']

_EXPORTS = {'PluginInstallService': ('src.logic.plugins.install.service', 'PluginInstallService'),
    'install_plugin': ('src.logic.plugins.install.service', 'install_plugin')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
