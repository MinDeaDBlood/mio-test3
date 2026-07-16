from __future__ import annotations

from threading import RLock
from typing import Any


class CurrentProjectState:
    """Application-owned reference to the current project variable."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._value: Any = None

    def bind(self, value: Any) -> None:
        if value is None:
            raise ValueError('current project state cannot be bound to None')
        with self._lock:
            self._value = value

    def require(self) -> Any:
        with self._lock:
            if self._value is None:
                raise RuntimeError('current project state is not bound')
            return self._value


current_project_state = CurrentProjectState()


__all__ = ['CurrentProjectState', 'current_project_state']
