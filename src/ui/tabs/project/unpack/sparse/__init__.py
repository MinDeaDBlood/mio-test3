from __future__ import annotations

from importlib import import_module

__all__ = ['SPEC', 'FORMAT', 'get_option_value', 'get_display_name', 'describe']

_EXPORT_MODULES = {
    'SPEC': '.view',
    'FORMAT': '.view',
    'get_option_value': '.view',
    'get_display_name': '.view',
    'describe': '.view',
}

def __getattr__(name: str):
    try:
        relative_module = _EXPORT_MODULES[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    module = import_module(relative_module, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value

