from __future__ import annotations

from importlib import import_module

__all__ = ['get_specs', 'get_option_values', 'has_option', 'get_spec']

_EXPORTS = {'get_specs': ('src.ui.tabs.project.unpack.registry', 'get_specs'),
    'get_option_values': ('src.ui.tabs.project.unpack.registry', 'get_option_values'),
    'has_option': ('src.ui.tabs.project.unpack.registry', 'has_option'),
    'get_spec': ('src.ui.tabs.project.unpack.registry', 'get_spec')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
