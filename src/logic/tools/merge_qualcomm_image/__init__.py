from __future__ import annotations

from importlib import import_module

__all__ = ['MergeQualcommRequest', 'ensure_output_dir', 'merge_by_rawprogram', 'validate_request']

_EXPORTS = {'MergeQualcommRequest': ('src.logic.tools.merge_qualcomm_image.service', 'MergeQualcommRequest'),
    'ensure_output_dir': ('src.logic.tools.merge_qualcomm_image.service', 'ensure_output_dir'),
    'merge_by_rawprogram': ('src.logic.tools.merge_qualcomm_image.service', 'merge_by_rawprogram'),
    'validate_request': ('src.logic.tools.merge_qualcomm_image.service', 'validate_request')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
