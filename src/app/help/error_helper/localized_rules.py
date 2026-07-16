from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.logic.help.error_helper.models import ErrorHelperRule

_PREFIX = 'error_helper_'
_PATTERNS_SUFFIX = '_patterns'
_DETAIL_SUFFIX = '_detail'
_SOLUTION_SUFFIX = '_solution'
_SEPARATOR = '||'


def error_helper_patterns_key(rule_id: str) -> str:
    return f'{_PREFIX}{rule_id}{_PATTERNS_SUFFIX}'


def error_helper_detail_key(rule_id: str) -> str:
    return f'{_PREFIX}{rule_id}{_DETAIL_SUFFIX}'


def error_helper_solution_key(rule_id: str) -> str:
    return f'{_PREFIX}{rule_id}{_SOLUTION_SUFFIX}'


def _rule_id_from_patterns_key(patterns_key: str) -> str:
    base_key = patterns_key[:-len(_PATTERNS_SUFFIX)]
    if base_key.startswith(_PREFIX):
        return base_key[len(_PREFIX):]
    return base_key


def _split_patterns(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(_SEPARATOR) if part.strip())
    if isinstance(value, (list, tuple)):
        return tuple(str(part).strip() for part in value if str(part).strip())
    return ()


def load_error_helper_rules_from_language_map(translations: Mapping[str, Any] | None) -> tuple[ErrorHelperRule, ...]:
    if not isinstance(translations, Mapping):
        return ()

    rules: list[ErrorHelperRule] = []
    pattern_keys = sorted(
        str(key)
        for key in translations
        if str(key).startswith(_PREFIX) and str(key).endswith(_PATTERNS_SUFFIX)
    )
    for patterns_key in pattern_keys:
        rule_id = _rule_id_from_patterns_key(patterns_key)
        patterns = _split_patterns(translations.get(patterns_key))
        detail = translations.get(error_helper_detail_key(rule_id))
        solution = translations.get(error_helper_solution_key(rule_id))
        if not patterns:
            continue
        if not isinstance(detail, str) or not detail.strip():
            continue
        if not isinstance(solution, str) or not solution.strip():
            continue
        rules.append(ErrorHelperRule(rule_id=rule_id, patterns=patterns))
    return tuple(rules)


__all__ = [
    'error_helper_detail_key',
    'error_helper_patterns_key',
    'error_helper_solution_key',
    'load_error_helper_rules_from_language_map',
]
