from __future__ import annotations

from importlib import import_module

__all__ = ['MagiskPatchRequest', 'build_output_path', 'get_arch', 'patch_boot_image', 'validate_request']

_EXPORTS = {'MagiskPatchRequest': ('src.logic.tools.magisk_patch.service', 'MagiskPatchRequest'),
    'build_output_path': ('src.logic.tools.magisk_patch.service', 'build_output_path'),
    'get_arch': ('src.logic.tools.magisk_patch.service', 'get_arch'),
    'patch_boot_image': ('src.logic.tools.magisk_patch.service', 'patch_boot_image'),
    'validate_request': ('src.logic.tools.magisk_patch.service', 'validate_request')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
