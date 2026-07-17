"""Operation context attached to every process log record."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar, Token
import logging
import time
from typing import Any
from uuid import uuid4

DEFAULT_OPERATION = 'process.startup'
_CURRENT_OPERATION: ContextVar[str] = ContextVar(
    'mio_current_operation', default=DEFAULT_OPERATION
)
_CURRENT_OPERATION_ID: ContextVar[str] = ContextVar(
    'mio_current_operation_id', default='startup'
)


class OperationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.operation = _CURRENT_OPERATION.get()
        record.operation_id = _CURRENT_OPERATION_ID.get()
        return True


OPERATION_FILTER = OperationFilter()


def current_operation() -> str:
    return _CURRENT_OPERATION.get()


def current_operation_id() -> str:
    return _CURRENT_OPERATION_ID.get()


def set_current_operation(name: str) -> Token[str]:
    normalized = str(name).strip() or DEFAULT_OPERATION
    return _CURRENT_OPERATION.set(normalized)


def reset_current_operation(token: Token[str]) -> None:
    _CURRENT_OPERATION.reset(token)


def render_details(details: Mapping[str, Any]) -> str:
    if not details:
        return ''
    return ', '.join(f'{key}={value!r}' for key, value in sorted(details.items()))


def _flush_handlers() -> None:
    for handler in logging.getLogger().handlers:
        try:
            handler.flush()
        except Exception:
            continue


@contextmanager
def operation_context(name: str, **details: Any) -> Iterator[None]:
    """Log one operation from start to completion with elapsed time and traceback."""
    token = set_current_operation(name)
    operation_id_token = _CURRENT_OPERATION_ID.set(uuid4().hex[:12])
    logger = logging.getLogger('mio.operation')
    detail_text = render_details(details)
    started = time.perf_counter()
    logger.info('Operation started%s', f': {detail_text}' if detail_text else '')
    try:
        yield
    except Exception:
        elapsed = time.perf_counter() - started
        logger.exception('Operation failed after %.3f seconds', elapsed)
        _flush_handlers()
        raise
    else:
        elapsed = time.perf_counter() - started
        logger.info('Operation completed in %.3f seconds', elapsed)
    finally:
        _CURRENT_OPERATION_ID.reset(operation_id_token)
        reset_current_operation(token)


__all__ = [
    'DEFAULT_OPERATION',
    'OPERATION_FILTER',
    'OperationFilter',
    'current_operation',
    'current_operation_id',
    'operation_context',
    'render_details',
    'reset_current_operation',
    'set_current_operation',
]
