from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorHelperRule:
    rule_id: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class ErrorHelperMatch:
    rule_id: str
    confidence: int
    source_text: str


__all__ = ['ErrorHelperMatch', 'ErrorHelperRule']
