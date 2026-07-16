from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import ErrorHelperMatch, ErrorHelperRule

_WORD_RE = re.compile(r"[\W_]+", re.UNICODE)


def normalize_text(value: str) -> str:
    text = str(value or '').lower()
    text = _WORD_RE.sub(' ', text)
    return ' '.join(text.split())


def confidence_for_pattern(source_text: str, pattern: str) -> int:
    source = normalize_text(source_text)
    normalized_pattern = normalize_text(pattern)
    if not source or not normalized_pattern:
        return 0
    if normalized_pattern in source:
        return 100
    return int(round(SequenceMatcher(None, normalized_pattern, source).quick_ratio() * 100))


def confidence_for_rule(source_text: str, rule: ErrorHelperRule) -> int:
    scores = [confidence_for_pattern(source_text, pattern) for pattern in rule.patterns]
    return max(scores, default=0)


def best_match(source_text: str, rules: tuple[ErrorHelperRule, ...], *, threshold: int) -> ErrorHelperMatch | None:
    normalized_threshold = max(0, min(100, int(threshold)))
    best_rule: ErrorHelperRule | None = None
    best_confidence = 0
    for rule in rules:
        confidence = confidence_for_rule(source_text, rule)
        if confidence > best_confidence:
            best_rule = rule
            best_confidence = confidence
        if confidence == 100:
            break
    if best_rule is None or best_confidence < normalized_threshold:
        return None
    return ErrorHelperMatch(
        rule_id=best_rule.rule_id,
        confidence=best_confidence,
        source_text=str(source_text),
    )


__all__ = ['best_match', 'confidence_for_pattern', 'confidence_for_rule', 'normalize_text']
