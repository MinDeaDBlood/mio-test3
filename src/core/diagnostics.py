from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from contextvars import ContextVar, Token
from typing import Any


DiagnosticSink = Callable[..., Any]
_LOGGER = logging.getLogger('mio.core')


def _logging_sink(
    *parts: object,
    sep: str = ' ',
    end: str = '\n',
    file: Any = None,
    flush: bool = False,
    **_kwargs: object,
) -> None:
    text = sep.join(str(part) for part in parts)
    if end and text.endswith(end):
        text = text[: -len(end)]
    level = logging.ERROR if file is sys.stderr else logging.INFO
    _LOGGER.log(level, text)
    if flush:
        for handler in logging.getLogger().handlers:
            handler.flush()


_default_sink: DiagnosticSink = _logging_sink
_override_sink: ContextVar[DiagnosticSink | None] = ContextVar('mio_core_diagnostic_sink', default=None)


def emit(*parts: object, **kwargs: object) -> Any:
    """Publish low level diagnostics through the configured boundary adapter."""

    sink = _override_sink.get() or _default_sink
    return sink(*parts, **kwargs)


def set_default_diagnostic_sink(sink: DiagnosticSink) -> None:
    """Set the process wide adapter used by core operations."""

    if not callable(sink):
        raise TypeError('Diagnostic sink must be callable')
    global _default_sink
    _default_sink = sink


def set_diagnostic_sink(sink: DiagnosticSink) -> Token:
    """Override diagnostics for the current execution context."""

    if not callable(sink):
        raise TypeError('Diagnostic sink must be callable')
    return _override_sink.set(sink)


def reset_diagnostic_sink(token: Token) -> None:
    _override_sink.reset(token)


__all__ = [
    'DiagnosticSink',
    'emit',
    'reset_diagnostic_sink',
    'set_default_diagnostic_sink',
    'set_diagnostic_sink',
]
