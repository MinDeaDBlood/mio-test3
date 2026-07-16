from __future__ import annotations

from importlib import import_module

__all__ = ['PackSuper', 'open_pack_super', 'pack_super']

_EXPORT_MODULES = {
    'PackSuper': '.view',
    'open_pack_super': '.view',
    'pack_super': '.view',
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

