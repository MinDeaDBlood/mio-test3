from __future__ import annotations

from importlib import import_module

__all__ = ['validate_workdir']

_EXPORTS = {'validate_workdir': ('src.logic.settings.validation.service', 'validate_workdir')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
