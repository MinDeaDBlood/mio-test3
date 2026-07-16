from __future__ import annotations

from importlib import import_module

__all__ = ['MpkStore']

_EXPORTS = {
    'MpkStore': ('src.ui.tabs.plugins.store.window', 'MpkStore'),
}


def __getattr__(name: str) -> object:
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
