from __future__ import annotations

from importlib import import_module

__all__ = ['BugReportRequest', 'generate_bug_report', 'normalize_output_dir']

_EXPORTS = {'BugReportRequest': ('src.logic.bug_report.service.service', 'BugReportRequest'),
    'generate_bug_report': ('src.logic.bug_report.service.service', 'generate_bug_report'),
    'normalize_output_dir': ('src.logic.bug_report.service.service', 'normalize_output_dir')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
