from __future__ import annotations

from importlib import import_module

__all__ = [
    'clear_log_output',
]

_EXPORTS = {
    'clear_log_output': ('src.ui.tabs.home.clear_log_button.button', 'clear_log_output'),
}

def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
