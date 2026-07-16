from __future__ import annotations

from threading import Lock


class OperationBusyError(RuntimeError):
    def __init__(self) -> None:
        super().__init__('Another operation is already running. Wait for it to finish before starting a new one.')


class OperationGate:
    """Allow only one resource intensive application operation at a time."""

    def __init__(self) -> None:
        self._lock = Lock()

    def try_acquire(self) -> bool:
        return self._lock.acquire(blocking=False)

    def release(self) -> None:
        if self._lock.locked():
            self._lock.release()

    def is_busy(self) -> bool:
        return self._lock.locked()


shared_operation_gate = OperationGate()


__all__ = ['OperationBusyError', 'OperationGate', 'shared_operation_gate']
