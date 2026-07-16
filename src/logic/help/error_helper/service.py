from __future__ import annotations

from collections.abc import Iterable

from .matcher import best_match
from .models import ErrorHelperMatch, ErrorHelperRule


def get_error_helper_match(
    text: str = '',
    *,
    threshold: int = 80,
    rules: Iterable[ErrorHelperRule] | None = None,
) -> ErrorHelperMatch | None:
    if not str(text or '').strip():
        return None
    resolved_rules = tuple(rules or ())
    if not resolved_rules:
        return None
    return best_match(str(text), resolved_rules, threshold=threshold)


__all__ = ['get_error_helper_match']
