from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import wraps
from threading import Thread
from tkinter import TclError
from typing import Any, Callable, Protocol

from src.app.operation_gate import OperationGate, shared_operation_gate


class LoadingAnimationPort(Protocol):
    master: Any | None

    def start(self, frame_index: int = 0) -> int: ...
    def stop(self) -> None: ...
    def initialize(self) -> None: ...
    def load_gif(self, gif: Any) -> None: ...


@dataclass(frozen=True)
class BackgroundTaskInfo:
    name: str
    args: tuple[Any, ...]
    thread: Thread


class AnimatedTaskRunner:
    """Run one heavy background job at a time and coordinate its animation."""

    def __init__(
        self,
        animation: LoadingAnimationPort,
        *,
        max_tasks: int = 1,
        operation_gate: OperationGate | None = None,
        on_busy: Callable[[], object] | None = None,
    ) -> None:
        self._animation = animation
        self._max_tasks = max(1, int(max_tasks))
        self._operation_gate = operation_gate or shared_operation_gate
        self._on_busy = on_busy
        self._tasks: dict[int, BackgroundTaskInfo] = {}
        self._next_index = -1

    @property
    def master(self) -> Any | None:
        return self._animation.master

    @master.setter
    def master(self, value: Any | None) -> None:
        self._animation.master = value

    @property
    def tasks(self) -> dict[int, BackgroundTaskInfo]:
        return self._tasks

    def has_tasks(self) -> bool:
        return bool(self._tasks)

    def load_gif(self, gif: Any) -> None:
        self._animation.load_gif(gif)

    def init(self) -> None:
        self._animation.initialize()

    def run(self) -> int:
        return self._animation.start()

    def stop(self) -> None:
        self._animation.stop()

    def _allocate_task_id(self) -> int:
        self._next_index = (self._next_index + 1) % self._max_tasks
        return self._next_index

    def _start_task(
        self,
        target: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> tuple[int, Thread] | None:
        if len(self._tasks) >= self._max_tasks or not self._operation_gate.try_acquire():
            return None
        try:
            task_id = self._allocate_task_id()
            thread = Thread(target=target, args=args, kwargs=kwargs, daemon=True)
            self._tasks[task_id] = BackgroundTaskInfo(
                name=(target.__name__ if hasattr(target, '__name__') else type(target).__name__),
                args=args,
                thread=thread,
            )
            thread.start()
            return task_id, thread
        except RuntimeError:
            self._operation_gate.release()
            raise

    def _complete(self, task_id: int) -> None:
        removed = self._tasks.pop(task_id, None)
        if removed is not None:
            self._operation_gate.release()
        if not self._tasks:
            self._animation.stop()

    def __call__(self, func: Callable[..., Any]):
        @wraps(func)
        def call_func(*args: Any, **kwargs: Any):
            started = self._start_task(func, args, kwargs)
            if started is None:
                logging.warning('A heavy operation is already running; task was not started: %s', func.__name__)
                if self._on_busy is not None:
                    try:
                        self._on_busy()
                    except Exception:
                        logging.exception('Unable to report a busy operation state')
                return False

            task_id, thread = started
            self._animation.start()

            def finish_when_done() -> None:
                master = self._animation.master
                if thread.is_alive():
                    if master is None:
                        thread.join()
                    else:
                        try:
                            master.after(50, finish_when_done)
                            return
                        except (RuntimeError, TclError):
                            logging.exception('Unable to schedule background-task completion check')
                self._complete(task_id)

            master = self._animation.master
            if master is None:
                finish_when_done()
            else:
                try:
                    master.after(50, finish_when_done)
                except (RuntimeError, TclError):
                    logging.exception('Unable to schedule background-task completion check')
                    self._complete(task_id)
            return None

        return call_func


__all__ = ['AnimatedTaskRunner', 'BackgroundTaskInfo', 'LoadingAnimationPort']
