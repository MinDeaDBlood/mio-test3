from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WelcomeNavigationLabels:
    back: str
    next: str
    finish: str


@dataclass(frozen=True)
class WelcomeNavigationState:
    back_enabled: bool
    next_text: str
    is_last: bool


class WelcomeNavigationPresenter:
    @staticmethod
    def build_state(*, step: int, frame_count: int, labels: WelcomeNavigationLabels) -> WelcomeNavigationState:
        if frame_count <= 0:
            raise ValueError('Welcome frame_count must be greater than zero.')
        is_last = step >= frame_count - 1
        return WelcomeNavigationState(
            back_enabled=step > 0,
            next_text=labels.finish if is_last else labels.next,
            is_last=is_last,
        )


__all__ = ['WelcomeNavigationLabels', 'WelcomeNavigationPresenter', 'WelcomeNavigationState']
