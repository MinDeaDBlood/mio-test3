from __future__ import annotations

from importlib import import_module

__all__ = ['bind_drop_target']

_EXPORTS = {
    'bind_drop_target': ('src.ui.tabs.home.drag_drop.view', 'bind_drop_target'),
}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
