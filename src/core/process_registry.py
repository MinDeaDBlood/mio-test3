from __future__ import annotations

from threading import RLock


class ProcessRegistry:
    """Thread-safe registry of child process identifiers."""

    def __init__(self) -> None:
        self._pids: list[int] = []
        self._lock = RLock()

    def add(self, pid: int) -> None:
        with self._lock:
            if pid not in self._pids:
                self._pids.append(pid)

    def discard(self, pid: int) -> None:
        with self._lock:
            if pid in self._pids:
                self._pids.remove(pid)

    def snapshot(self) -> tuple[int, ...]:
        with self._lock:
            return tuple(self._pids)

    @property
    def items(self) -> list[int]:
        return self._pids


process_registry = ProcessRegistry()

__all__ = ['ProcessRegistry', 'process_registry']
