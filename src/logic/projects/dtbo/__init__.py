from __future__ import annotations

from importlib import import_module

__all__ = ['DtboRuntimeContext', 'build_runtime_context', 'pack_dtbo', 'unpack_dtbo']

_EXPORTS = {'DtboRuntimeContext': ('src.logic.projects.dtbo.service', 'DtboRuntimeContext'),
    'build_runtime_context': ('src.logic.projects.dtbo.service', 'build_runtime_context'),
    'pack_dtbo': ('src.logic.projects.dtbo.service', 'pack_dtbo'),
    'unpack_dtbo': ('src.logic.projects.dtbo.service', 'unpack_dtbo')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
