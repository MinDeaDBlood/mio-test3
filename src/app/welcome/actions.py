from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable


@dataclass(frozen=True)
class WelcomeActions:
    choose_workdir: Callable[[], str]
    open_workdir: Callable[[str], object]
    apply_language: Callable[[str], object]
    set_oobe_active: Callable[[bool], object]


__all__ = ['WelcomeActions']
