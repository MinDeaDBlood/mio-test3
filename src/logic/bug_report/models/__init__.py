from __future__ import annotations

from importlib import import_module

__all__ = ['BugReportMeta']

_EXPORTS = {'BugReportMeta': ('src.logic.bug_report.models.report_models', 'BugReportMeta')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
