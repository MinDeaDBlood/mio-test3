from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol

from src.ui.localization import LocalizationCatalog
from src.ui.common.formatting import enum_value
from src.ui import startup_issue_keys as keys


class StartupIssueProtocol(Protocol):
    @property
    def code(self) -> object: ...


def _issue_code_value(issue: StartupIssueProtocol) -> str:
    return str(enum_value(issue.code))


def present_startup_issues(
    issues: Iterable[StartupIssueProtocol],
    *,
    texts: LocalizationCatalog,
    show_fatal: Callable[[int, str], object],
    confirm_warning: Callable[..., object],
) -> None:
    for issue in issues:
        code = _issue_code_value(issue)
        if code == "unsupported-platform":
            show_fatal(
                1, texts.resolve_required_ui_text(keys.UNSUPPORTED_PLATFORM_MESSAGE)
            )
        elif code == "non-printable-workspace":
            confirm_warning(
                texts.resolve_required_ui_text(keys.ROOT_PERMISSION_MESSAGE_FORMAT)
                % texts.resolve_required_ui_text(keys.ROOT_PERMISSION_NAME),
                is_top=True,
            )


__all__ = ["present_startup_issues"]
