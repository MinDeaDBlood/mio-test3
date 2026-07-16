"""Application boundary for background-job lifecycle policy."""

from __future__ import annotations

from collections.abc import Callable
from threading import Thread
from typing import Any


def start_background_job(
    func: Callable[..., Any],
    *args: Any,
    join: bool = False,
    daemon: bool = True,
) -> Thread:
    """Start one application-managed background job and return its thread."""
    thread = Thread(target=func, args=args, daemon=daemon)
    thread.start()
    if join:
        thread.join()
    return thread


__all__ = ['start_background_job']
