from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from src.app.runtime.contexts.contracts import (
    HostWindowProtocol,
    MessagePopProtocol,
    SchedulerHostProtocol,
)
from src.app.runtime.contexts.ui import (
    resolve_default_message_pop,
    resolve_ui_host_window,
    resolve_ui_scheduler,
)

UiCallback = Callable[..., object]


class SchedulerProtocol(Protocol):
    def __call__(
        self,
        callback: UiCallback,
        args: tuple[object, ...],
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class UiNotifier:
    message_pop: MessagePopProtocol

    def show(
        self,
        message: str | None = None,
        color: str | None = None,
        *,
        text: str | None = None,
        title: str | None = None,
        master: object | None = None,
    ) -> object:
        resolved_text = text if text is not None else (message or '')
        resolved_color = color or 'red'
        return self.message_pop(
            text=resolved_text,
            color=resolved_color,
            title=title,
            master=master,
        )

    __call__ = show


@dataclass(frozen=True, slots=True)
class UiDispatcher:
    schedule: SchedulerProtocol
    start: Callable[[], bool]
    stop: Callable[[], bool]

    def dispatch(self, callback: UiCallback, *args: object) -> bool:
        return self.schedule(callback, args)


def build_ui_notifier(
    message_pop: MessagePopProtocol | None = None,
    *,
    host_window: HostWindowProtocol | None = None,
) -> UiNotifier:
    resolved = message_pop or resolve_default_message_pop(
        host_window=host_window
    )
    if not callable(resolved):
        raise RuntimeError(
            'UI notifier requires a callable message_pop implementation.'
        )
    return UiNotifier(message_pop=resolved)


def build_ui_dispatcher(
    *,
    host_window: SchedulerHostProtocol | None = None,
    scheduler: SchedulerProtocol | None = None,
) -> UiDispatcher:
    if scheduler is not None:
        return UiDispatcher(
            schedule=scheduler,
            start=lambda: True,
            stop=lambda: True,
        )
    host = resolve_ui_host_window(host_window)
    app_scheduler = resolve_ui_scheduler(host)
    return UiDispatcher(
        schedule=app_scheduler.post,
        start=app_scheduler.start,
        stop=app_scheduler.stop,
    )


__all__ = [
    'SchedulerProtocol',
    'UiDispatcher',
    'UiNotifier',
    'build_ui_dispatcher',
    'build_ui_notifier',
]
