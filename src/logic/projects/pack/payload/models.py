from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PayloadPackAction:
    name: str = 'payload'
    description: str = 'payload packing action'
    implemented: bool = False
    supported_platforms: tuple[str, ...] = ()


@dataclass(frozen=True)
class PayloadPackImplementationAudit:
    has_registered_pipeline: bool
    has_generator_backend: bool
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class PayloadPackCapability:
    available: bool
    platform_name: str
    reason: str
    audit: PayloadPackImplementationAudit | None = None


class PayloadPackUnavailable(RuntimeError):
    """Raised when payload packing is requested on an unsupported platform."""

    def __init__(self, capability: PayloadPackCapability):
        super().__init__(capability.reason)
        self.capability = capability


__all__ = [
    'PayloadPackAction',
    'PayloadPackImplementationAudit',
    'PayloadPackCapability',
    'PayloadPackUnavailable',
]
