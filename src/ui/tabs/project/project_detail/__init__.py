from __future__ import annotations

from importlib import import_module

__all__ = ['current_project_details']

_EXPORT_MODULES = {
    'current_project_details': '.view',
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

