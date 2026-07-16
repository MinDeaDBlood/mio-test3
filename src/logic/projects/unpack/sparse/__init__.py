from __future__ import annotations

from importlib import import_module

__all__ = ['execute', 'list_candidates', 'get_format_name']

_EXPORT_MODULES = {
    'execute': '.controller',
    'list_candidates': '.controller',
    'get_format_name': '.controller',
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

