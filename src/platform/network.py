from __future__ import annotations

from types import ModuleType


def load_requests_module() -> ModuleType:
    """Load the optional HTTP client at the platform boundary."""

    import requests

    return requests


__all__ = ["load_requests_module"]
