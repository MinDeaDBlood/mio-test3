from __future__ import annotations

from threading import Lock
from typing import Callable, Generic, TypeVar

from src.app.ui_feedback import UiDispatcher

T = TypeVar('T')


class UiCoalescedDrain(Generic[T]):
    """Coalesce background signals into UI-thread drain callbacks.

    Producers call :meth:`notify` whenever new items were enqueued into a bounded
    queue/stream. The relay schedules at most one UI-thread drain at a time and
    lets the consumer batch visible updates.
    """

    def __init__(
        self,
        *,
        dispatcher: UiDispatcher,
        drain: Callable[[], list[T]],
        consume: Callable[[list[T]], None],
        is_alive: Callable[[], bool] | None = None,
        logger=None,
    ) -> None:
        self.dispatcher = dispatcher
        self.drain = drain
        self.consume = consume
        self.is_alive = is_alive or (lambda: True)
        self.logger = logger
        self._lock = Lock()
        self._scheduled = False
        self._closed = False

    def notify(self) -> bool:
        with self._lock:
            if self._closed:
                return False
            if self._scheduled:
                return True
            self._scheduled = True
        if self.dispatcher.dispatch(self._flush_on_ui):
            return True
        with self._lock:
            self._scheduled = False
        return False

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._scheduled = False

    def _flush_on_ui(self) -> None:
        while True:
            with self._lock:
                self._scheduled = False
                closed = self._closed
            if closed or not self.is_alive():
                return
            try:
                items = self.drain()
            except Exception:
                if self.logger:
                    self.logger.exception('UiCoalescedDrain._flush_on_ui drain failed')
                return
            if items:
                try:
                    self.consume(items)
                except Exception:
                    if self.logger:
                        self.logger.exception('UiCoalescedDrain._flush_on_ui consume failed')
                    return
            with self._lock:
                if self._closed:
                    return
                rescheduled = self._scheduled
            if not rescheduled:
                return


__all__ = [
    'UiCoalescedDrain',
]
