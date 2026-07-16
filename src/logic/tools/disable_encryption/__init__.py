from __future__ import annotations

from importlib import import_module

__all__ = ['patch_fstab_files', 'patch_selected_partitions', 'scan_project_for_fstab_partitions']

_EXPORTS = {'patch_fstab_files': ('src.logic.tools.disable_encryption.service', 'patch_fstab_files'),
    'patch_selected_partitions': ('src.logic.tools.disable_encryption.service', 'patch_selected_partitions'),
    'scan_project_for_fstab_partitions': ('src.logic.tools.disable_encryption.service', 'scan_project_for_fstab_partitions')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
