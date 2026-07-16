from __future__ import annotations

from src.platform.filesystem import path_exists
from src.logic.startup import StartupIssue, StartupIssueCode


def collect_startup_issues(settings) -> tuple[StartupIssue, ...]:
    issues: list[StartupIssue] = []
    if not path_exists(settings.tool_bin):
        issues.append(StartupIssue(StartupIssueCode.UNSUPPORTED_PLATFORM, settings.tool_bin))
    if not settings.path.isprintable():
        issues.append(StartupIssue(StartupIssueCode.NON_PRINTABLE_WORKSPACE, settings.path))
    return tuple(issues)


__all__ = ['StartupIssue', 'StartupIssueCode', 'collect_startup_issues']
