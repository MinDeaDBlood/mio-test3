from __future__ import annotations

from importlib import import_module

__all__ = ['BootImageRuntimeContext', 'build_runtime_context', 'repack_boot_image', 'unpack_boot_image']

_EXPORTS = {'BootImageRuntimeContext': ('src.logic.projects.boot_images.runtime_context', 'BootImageRuntimeContext'),
    'build_runtime_context': ('src.logic.projects.boot_images.runtime_context', 'build_runtime_context'),
    'repack_boot_image': ('src.logic.projects.boot_images.service', 'repack_boot_image'),
    'unpack_boot_image': ('src.logic.projects.boot_images.service', 'unpack_boot_image')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
