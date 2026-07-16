from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from src.logic.common.messages import LogicMessage


class OutputChannel(str, Enum):
    LOG = 'log'
    STATUS = 'status'


class OutputSeverity(str, Enum):
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'


@dataclass(frozen=True)
class ServiceOutputEvent:
    message: object
    channel: OutputChannel = OutputChannel.LOG
    severity: OutputSeverity = OutputSeverity.INFO


class OutputEventSink(Protocol):
    def __call__(self, event: ServiceOutputEvent) -> object: ...


def _render_default(value: object) -> str:
    if isinstance(value, LogicMessage):
        return value.render_default()
    return str(value)


def _default_event_sink(event: ServiceOutputEvent) -> None:
    logger = logging.getLogger('mio.logic')
    level = {
        OutputSeverity.INFO: logging.INFO,
        OutputSeverity.SUCCESS: logging.INFO,
        OutputSeverity.WARNING: logging.WARNING,
        OutputSeverity.ERROR: logging.ERROR,
    }[event.severity]
    logger.log(
        level,
        'channel=%s severity=%s message=%s',
        event.channel.value,
        event.severity.value,
        _render_default(event.message),
    )


@dataclass(frozen=True)
class ServiceOutput:
    """Publishes semantic operation events without depending on UI or localization."""

    emit: OutputEventSink = _default_event_sink

    def log(self, *parts: object, severity: OutputSeverity = OutputSeverity.INFO) -> None:
        if not parts:
            return
        message_value: object
        if len(parts) == 1:
            message_value = parts[0]
        else:
            message_value = ' '.join(_render_default(part) for part in parts)
        self.emit(ServiceOutputEvent(message=message_value, channel=OutputChannel.LOG, severity=severity))

    def report(self, message: object, *, severity: OutputSeverity = OutputSeverity.INFO) -> None:
        self.emit(ServiceOutputEvent(message=message, channel=OutputChannel.STATUS, severity=severity))

    def log_and_report(self, message: object, *, severity: OutputSeverity = OutputSeverity.INFO) -> None:
        self.log(message, severity=severity)
        self.report(message, severity=severity)


def build_service_output(*, emit: OutputEventSink | None = None) -> ServiceOutput:
    return ServiceOutput(emit=emit or _default_event_sink)


__all__ = [
    'OutputChannel',
    'OutputEventSink',
    'OutputSeverity',
    'ServiceOutput',
    'ServiceOutputEvent',
    'build_service_output',
]
