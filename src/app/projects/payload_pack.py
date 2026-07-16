from __future__ import annotations

from dataclasses import dataclass

from src.logic.projects.pack.payload.models import PayloadPackCapability


@dataclass(frozen=True)
class PayloadPackLaunchResult:
    opened: bool
    capability: PayloadPackCapability
    window: object | None = None


__all__ = ['PayloadPackLaunchResult']
