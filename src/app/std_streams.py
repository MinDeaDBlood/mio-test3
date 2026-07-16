"""Process stream routing owned by the application layer.

The legacy UI used to rebind ``sys.stdout``/``sys.stderr`` from view modules.
That made startup order implicit and leaked process-wide side effects into the
right panel and crash windows. The application layer now owns the process
stream boundary and UI code only attaches/detaches sinks explicitly.
"""

from __future__ import annotations

import logging
import sys
from itertools import count
from threading import RLock
from typing import Any, TextIO


class StreamRouter:
    def __init__(self, *, name: str, origin: TextIO | None):
        self.name = name
        self.origin = origin
        self.data = ''
        self._lock = RLock()
        self._sinks: dict[int, Any] = {}

    @property
    def encoding(self):
        if self.origin is None or not hasattr(self.origin, 'encoding'):
            return None
        return self.origin.encoding

    def attach_sink(self, sink) -> callable:
        token = next(_SINK_IDS)
        with self._lock:
            self._sinks[token] = sink

        def detach() -> None:
            self.detach_sink(token)

        return detach

    def detach_sink(self, token: int) -> None:
        with self._lock:
            self._sinks.pop(token, None)

    def write(self, value) -> int:
        if value is None:
            return 0
        text = str(value)
        if not text:
            return 0
        sinks = []
        with self._lock:
            self.data += text
            sinks = list(self._sinks.values())
        self._write_origin(text)
        self._broadcast('write', text, sinks)
        return len(text)

    def flush(self) -> None:
        sinks = []
        with self._lock:
            sinks = list(self._sinks.values())
        try:
            if self.origin is not None and hasattr(self.origin, 'flush'):
                self.origin.flush()
        except Exception:
            pass
        self._broadcast('flush', None, sinks)

    def isatty(self) -> bool:
        origin = self.origin
        if origin is None or not hasattr(origin, 'isatty'):
            return False
        try:
            return bool(origin.isatty())
        except Exception:
            return False

    def fileno(self) -> int:
        origin = self.origin
        if origin is None or not hasattr(origin, 'fileno'):
            raise OSError(f'{self.name} has no file descriptor')
        return origin.fileno()

    def _write_origin(self, text: str) -> None:
        origin = self.origin
        if origin is None or origin is self:
            return
        try:
            origin.write(text)
        except Exception:
            pass

    @staticmethod
    def _broadcast(method_name: str, value, sinks: list[Any]) -> None:
        for sink in sinks:
            try:
                if method_name == 'write' and hasattr(sink, 'write'):
                    sink.write(value)
                elif method_name == 'flush' and hasattr(sink, 'flush'):
                    sink.flush()
            except Exception:
                continue


class _LineLoggingSink:
    def __init__(self, *, logger_name: str, level: int):
        self._logger = logging.getLogger(logger_name)
        self._level = level
        self._buffer = ''
        self._lock = RLock()

    def write(self, value) -> int:
        text = str(value or '')
        if not text:
            return 0
        with self._lock:
            self._buffer += text
            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                if line.strip():
                    self._logger.log(self._level, '%s', line.rstrip())
        return len(text)

    def flush(self) -> None:
        with self._lock:
            if self._buffer.strip():
                self._logger.log(self._level, '%s', self._buffer.rstrip())
            self._buffer = ''


_SINK_IDS = count(1)
_STREAMS: dict[str, StreamRouter] = {}
_LOGGING_SINKS_ATTACHED = False


def _origin_for_stream(name: str):
    attr = f'{name}_origin'
    origin = getattr(sys, attr) if hasattr(sys, attr) else None
    if origin is not None:
        return origin
    backup_attr = f'__{name}__'
    backup_stream = getattr(sys, backup_attr) if hasattr(sys, backup_attr) else None
    current = getattr(sys, name) if hasattr(sys, name) else None
    if current is not None and current is not backup_stream:
        origin = current
    else:
        origin = backup_stream or current
    setattr(sys, attr, origin)
    return origin


def ensure_process_streams_installed() -> dict[str, StreamRouter]:
    global _LOGGING_SINKS_ATTACHED
    for name in ('stdout', 'stderr'):
        router = _STREAMS.get(name)
        if router is None:
            router = StreamRouter(name=name, origin=_origin_for_stream(name))
            _STREAMS[name] = router
        setattr(sys, name, router)
    if not _LOGGING_SINKS_ATTACHED:
        _STREAMS['stdout'].attach_sink(
            _LineLoggingSink(logger_name='mio.stdout', level=logging.INFO)
        )
        _STREAMS['stderr'].attach_sink(
            _LineLoggingSink(logger_name='mio.stderr', level=logging.ERROR)
        )
        _LOGGING_SINKS_ATTACHED = True
    return dict(_STREAMS)


def resolve_stream_router(name: str) -> StreamRouter:
    streams = ensure_process_streams_installed()
    return streams[name]


def attach_stream_sink(name: str, sink) -> callable:
    return resolve_stream_router(name).attach_sink(sink)


def get_stdout_router() -> StreamRouter:
    return resolve_stream_router('stdout')


def get_stderr_router() -> StreamRouter:
    return resolve_stream_router('stderr')


__all__ = [
    'StreamRouter',
    'attach_stream_sink',
    'ensure_process_streams_installed',
    'get_stderr_router',
    'get_stdout_router',
    'resolve_stream_router',
]
