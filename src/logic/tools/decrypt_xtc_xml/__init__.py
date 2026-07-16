from __future__ import annotations

from importlib import import_module

__all__ = ['decrypt_tree']

_EXPORTS = {'decrypt_tree': ('src.logic.tools.decrypt_xtc_xml.service', 'decrypt_tree')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
