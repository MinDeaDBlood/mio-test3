"""Application boundary for background job lifecycle policy."""

from __future__ import annotations

from collections.abc import Callable
from contextvars import copy_context
import logging
from threading import Thread
from typing import Any

from src.platform.crash_logging import operation_context

logger = logging.getLogger(__name__)


def describe_callable(func: Callable[..., Any]) -> str:
    module = func.__module__ if hasattr(func, '__module__') else '<unknown>'
    if hasattr(func, '__qualname__'):
        qualname = func.__qualname__
    elif hasattr(func, '__name__'):
        qualname = func.__name__
    else:
        qualname = repr(func)
    return f'{module}.{qualname}'


def _thread_label(func: Callable[..., Any]) -> str:
    return func.__name__ if hasattr(func, '__name__') else 'worker'


def start_background_job(
    func: Callable[..., Any],
    *args: Any,
    join: bool = False,
    daemon: bool = True,
) -> Thread:
    """Start one application managed background job and return its thread."""
    operation_name = f'background:{describe_callable(func)}'
    context = copy_context()

    def run_job() -> None:
        with operation_context(operation_name, daemon=daemon):
            context.run(func, *args)

    thread = Thread(
        target=run_job,
        daemon=daemon,
        name=f'MIO:{_thread_label(func)}',
    )
    logger.debug(
        'Starting background thread: name=%s daemon=%s target=%s',
        thread.name,
        daemon,
        describe_callable(func),
    )
    thread.start()
    if join:
        thread.join()
        logger.debug('Background thread joined: name=%s', thread.name)
    return thread


__all__ = ['describe_callable', 'start_background_job']
