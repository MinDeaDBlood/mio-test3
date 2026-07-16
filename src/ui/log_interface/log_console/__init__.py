from __future__ import annotations

from importlib import import_module

__all__ = ['append_log', 'clear_log']

_EXPORTS = {'append_log': ('src.ui.log_interface.log_console.view', 'append_log'),
    'clear_log': ('src.ui.log_interface.log_console.view', 'clear_log')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
