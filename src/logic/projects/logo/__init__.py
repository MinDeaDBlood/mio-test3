from __future__ import annotations

from importlib import import_module

__all__ = ['LogoRuntimeContext', 'build_runtime_context', 'dump_logo', 'pack_logo']

_EXPORTS = {'LogoRuntimeContext': ('src.logic.projects.logo.service', 'LogoRuntimeContext'),
    'build_runtime_context': ('src.logic.projects.logo.service', 'build_runtime_context'),
    'dump_logo': ('src.logic.projects.logo.service', 'dump_logo'),
    'pack_logo': ('src.logic.projects.logo.service', 'pack_logo')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
