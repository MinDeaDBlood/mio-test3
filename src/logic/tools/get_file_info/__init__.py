from __future__ import annotations

from importlib import import_module

__all__ = ['describe_path']

_EXPORTS = {'describe_path': ('src.logic.tools.get_file_info.service', 'describe_path')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
