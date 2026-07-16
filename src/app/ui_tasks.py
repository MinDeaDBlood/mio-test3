from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import logging
from typing import TypeVar

from src.app.background_jobs import describe_callable, start_background_job
from src.app.operation_gate import OperationBusyError, OperationGate, shared_operation_gate
from src.app.ui_feedback import UiDispatcher
from src.core.contracts import LoggerProtocol

T = TypeVar('T')

logger = logging.getLogger(__name__)


WorkerStarterProtocol = Callable[..., object]


@dataclass(frozen=True, slots=True)
class UiTaskRunner:
    """Run background work and finalize through the shared UI dispatcher."""

    dispatcher: UiDispatcher
    is_alive: Callable[[], bool] = lambda: True
    logger: LoggerProtocol | None = None
    start_worker: WorkerStarterProtocol = start_background_job
    operation_gate: OperationGate = shared_operation_gate

    def _dispatch_busy(
        self,
        on_busy: Callable[[], object] | None,
        on_error: Callable[[Exception], object] | None,
        on_finally: Callable[[], object] | None,
    ) -> None:
        busy_callback = on_busy
        if busy_callback is None and on_error is not None:
            def busy_callback() -> object:
                return on_error(OperationBusyError())
        if busy_callback is None and self.logger is not None:
            self.logger.warning('UiTaskRunner.run rejected because another heavy operation is running')

        def finalize_busy() -> object:
            try:
                if self.is_alive() and busy_callback is not None:
                    return busy_callback()
                return None
            finally:
                self._run_finally(on_finally)

        if busy_callback is not None or on_finally is not None:
            self.dispatcher.dispatch(finalize_busy)

    def _run_finally(self, callback: Callable[[], object] | None) -> None:
        if callback is None:
            return
        try:
            callback()
        except Exception:
            if self.logger is not None:
                self.logger.exception('UiTaskRunner.run finalizer failed')

    def run(
        self,
        worker: Callable[..., T],
        *args: object,
        worker_kwargs: Mapping[str, object] | None = None,
        on_success: Callable[[T], object] | None = None,
        on_error: Callable[[Exception], object] | None = None,
        on_finally: Callable[[], object] | None = None,
        on_busy: Callable[[], object] | None = None,
        exclusive: bool = False,
        daemon: bool = True,
    ) -> bool | None:
        gate_acquired = False
        if exclusive:
            gate_acquired = self.operation_gate.try_acquire()
            if not gate_acquired:
                self._dispatch_busy(on_busy, on_error, on_finally)
                return False

        keyword_args = dict(worker_kwargs or {})

        def finalize_error(error: Exception) -> object:
            callback_result = None
            try:
                if self.is_alive() and on_error is not None:
                    callback_result = on_error(error)
                return callback_result
            finally:
                self._run_finally(on_finally)

        def finalize_success(result: T) -> object:
            callback_result = None
            try:
                if self.is_alive() and on_success is not None:
                    callback_result = on_success(result)
                return callback_result
            finally:
                self._run_finally(on_finally)

        worker_name = describe_callable(worker)
        active_logger = self.logger or logger

        def worker_target() -> None:
            active_logger.info(
                'UiTaskRunner worker started: worker=%s exclusive=%s daemon=%s',
                worker_name,
                exclusive,
                daemon,
            )
            try:
                result = worker(*args, **keyword_args)
            except Exception as error:
                active_logger.exception('UiTaskRunner.run worker failed: %s', worker_name)
                if on_error is not None or on_finally is not None:
                    self.dispatcher.dispatch(finalize_error, error)
                return
            finally:
                if gate_acquired:
                    self.operation_gate.release()

            active_logger.info('UiTaskRunner worker completed: %s', worker_name)
            if on_success is not None or on_finally is not None:
                self.dispatcher.dispatch(finalize_success, result)

        try:
            self.start_worker(worker_target, daemon=daemon)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            if gate_acquired:
                self.operation_gate.release()
            (self.logger or logger).exception('UiTaskRunner.run could not start worker: %s', worker_name)
            if on_error is not None or on_finally is not None:
                self.dispatcher.dispatch(finalize_error, error)
            return False
        return None

    def fire_and_forget(
        self,
        worker: Callable[..., object],
        *args: object,
        worker_kwargs: Mapping[str, object] | None = None,
        on_busy: Callable[[], object] | None = None,
        exclusive: bool = False,
        daemon: bool = True,
    ) -> bool | None:
        return self.run(
            worker,
            *args,
            worker_kwargs=worker_kwargs,
            on_busy=on_busy,
            exclusive=exclusive,
            daemon=daemon,
        )


def build_ui_task_runner(
    *,
    dispatcher: UiDispatcher,
    is_alive: Callable[[], bool] | None = None,
    logger: LoggerProtocol | None = None,
    start_worker: WorkerStarterProtocol | None = None,
    operation_gate: OperationGate | None = None,
) -> UiTaskRunner:
    return UiTaskRunner(
        dispatcher=dispatcher,
        is_alive=is_alive or (lambda: True),
        logger=logger,
        start_worker=start_worker or start_background_job,
        operation_gate=operation_gate or shared_operation_gate,
    )


__all__ = [
    'UiTaskRunner',
    'WorkerStarterProtocol',
    'build_ui_task_runner',
]
