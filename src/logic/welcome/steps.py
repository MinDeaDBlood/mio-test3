from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WelcomeStepPolicy:
    """Domain rule for valid initial setup steps."""

    frame_count: int

    def __post_init__(self) -> None:
        if self.frame_count <= 0:
            raise ValueError("Welcome frame_count must be greater than zero.")

    def clamp(self, step: int) -> int:
        if not isinstance(step, int):
            raise TypeError("Welcome step must be an integer.")
        return max(0, min(step, self.frame_count - 1))


__all__ = ["WelcomeStepPolicy"]
