from __future__ import annotations

from importlib import import_module

__all__ = ['existing_attachments']

_EXPORTS = {'existing_attachments': ('src.logic.bug_report.attachments.service', 'existing_attachments')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
