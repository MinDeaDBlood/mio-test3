from __future__ import annotations

from importlib import import_module

__all__ = ['run_selinux_audit_allow']

_EXPORTS = {'run_selinux_audit_allow': ('src.logic.tools.allow_selinux_audit.service', 'run_selinux_audit_allow')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
