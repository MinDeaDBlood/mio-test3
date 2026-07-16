from __future__ import annotations


class MissingRuntimeValueError(RuntimeError):
    """Raised when required runtime state is accessed before bootstrap."""


class UnknownRuntimeKeyError(KeyError):
    """Raised when code attempts to register a runtime key outside the approved registry."""


__all__ = ['MissingRuntimeValueError', 'UnknownRuntimeKeyError']
