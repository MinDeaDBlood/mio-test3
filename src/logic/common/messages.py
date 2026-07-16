from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class LogicMessage:
    """Semantic message produced by logic without depending on localization or UI."""

    code: str
    default: str
    params: Mapping[str, object] = field(default_factory=dict)

    def render_default(self) -> str:
        try:
            return self.default.format(**self.params)
        except (KeyError, ValueError, IndexError):
            return self.default


def message(code: str, default: str, **params: object) -> LogicMessage:
    return LogicMessage(code=code, default=default, params=params)


__all__ = ['LogicMessage', 'message']
