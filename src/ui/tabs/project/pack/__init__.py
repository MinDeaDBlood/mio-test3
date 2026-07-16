from __future__ import annotations

from importlib import import_module

__all__ = ['get_specs', 'get_output_values']

_EXPORTS = {'get_specs': ('src.ui.tabs.project.pack.registry', 'get_specs'),
    'get_output_values': ('src.ui.tabs.project.pack.registry', 'get_output_values')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
