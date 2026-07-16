from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StartupIssueCode(str, Enum):
    UNSUPPORTED_PLATFORM = 'unsupported-platform'
    NON_PRINTABLE_WORKSPACE = 'non-printable-workspace'


@dataclass(frozen=True)
class StartupIssue:
    code: StartupIssueCode
    detail: str = ''


__all__ = ['StartupIssue', 'StartupIssueCode']
