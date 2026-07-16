from __future__ import annotations

from dataclasses import dataclass, field
import logging
from queue import Empty, SimpleQueue
from threading import Lock, current_thread, main_thread
from collections.abc import Callable
from typing import cast
from tkinter import TclError

from src.app.runtime.contexts.contracts import SchedulerHostProtocol
from src.app.runtime.phases import sync_registered_bootstrap_window_runtime
from src.app.runtime.window_access import get_ui_scheduler

logger = logging.getLogger(__name__)

UiCallback = Callable[..., object]


def _resolve_scheduler_host(
    host_window: SchedulerHostProtocol | None,
) -> SchedulerHostProtocol | None:
    if host_window is None:
        return None
    try:
        top_level = host_window.winfo_toplevel()
    except (AttributeError, RuntimeError, TclError):
        return host_window
    return top_level or host_window


@dataclass
class AppUiScheduler:
    host_window: SchedulerHostProtocol | None
    poll_ms: int = 15
    _queue: SimpleQueue[tuple[UiCallback, tuple[object, ...]]] = field(
        default_factory=SimpleQueue
    )
    _lock: Lock = field(default_factory=Lock)
    _pump_id: str | None = None

    def attach(self, host_window: SchedulerHostProtocol) -> bool:
        resolved = _resolve_scheduler_host(host_window)
        if resolved is None:
            return False
        current = self.host_window
        if current is resolved:
            return True
        if current is not None:
            try:
                if current.winfo_exists():
                    return True
            except (AttributeError, RuntimeError, TclError):
                pass
        self.host_window = resolved
        return True

    def start(self) -> bool:
        if current_thread() is not main_thread():
            return self._pump_id is not None
        if self._pump_id is not None:
            return True
        return self._schedule_next()

    def stop(self) -> bool:
        pump_id = self._pump_id
        self._pump_id = None
        if pump_id is None:
            return True
        try:
            host_window = self.host_window
            if host_window is not None and host_window.winfo_exists():
                host_window.after_cancel(pump_id)
            return True
        except (AttributeError, RuntimeError, TclError):
            return False

    def post(
        self,
        callback: UiCallback,
        args: tuple[object, ...] = (),
    ) -> bool:
        if current_thread() is main_thread():
            callback(*args)
            return True
        self._queue.put((callback, args))
        return True

    def _schedule_next(self) -> bool:
        host_window = self.host_window
        if host_window is None:
            self._pump_id = None
            return False
        try:
            if not host_window.winfo_exists():
                self._pump_id = None
                return False
            self._pump_id = host_window.after(self.poll_ms, self._drain)
            return True
        except (AttributeError, RuntimeError, TclError):
            self._pump_id = None
            return False

    def _drain(self) -> None:
        self._pump_id = None
        while True:
            try:
                callback, args = self._queue.get_nowait()
            except Empty:
                break
            try:
                callback(*args)
            except Exception:
                logger.exception(
                    'AppUiScheduler callback failed: %r',
                    callback,
                )
                continue
        self._schedule_next()


def initialize_app_ui_scheduler(
    host_window: SchedulerHostProtocol,
    *,
    poll_ms: int = 15,
) -> AppUiScheduler:
    registered = get_ui_scheduler()
    if registered is None:
        resolved_host = _resolve_scheduler_host(host_window)
        scheduler = AppUiScheduler(
            host_window=resolved_host,
            poll_ms=poll_ms,
        )
        sync_registered_bootstrap_window_runtime(
            main_window=resolved_host,
            ui_scheduler=scheduler,
        )
    else:
        scheduler = cast(AppUiScheduler, registered)
        scheduler.attach(host_window)
    scheduler.start()
    return scheduler


def resolve_app_ui_scheduler(
    host_window: SchedulerHostProtocol | None = None,
) -> AppUiScheduler:
    registered = get_ui_scheduler()
    if registered is None:
        if host_window is None:
            raise RuntimeError(
                'UI scheduler is not initialized and no host window was provided'
            )
        return initialize_app_ui_scheduler(host_window)

    scheduler = cast(AppUiScheduler, registered)
    if host_window is not None:
        scheduler.attach(host_window)
        scheduler.start()
    return scheduler


__all__ = [
    'AppUiScheduler',
    'UiCallback',
    'initialize_app_ui_scheduler',
    'resolve_app_ui_scheduler',
]
