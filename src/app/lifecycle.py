"""Application lifecycle operations with explicit presentation callbacks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.app.process_lifecycle import exit_tool as _exit_tool
from src.app.process_lifecycle import restart as _restart


def restart_app(
    window: Any | None = None,
    *,
    confirm_unsaved: Callable[[], bool] | None = None,
) -> bool:
    return _restart(window, confirm_unsaved=confirm_unsaved)


def exit_app() -> Any:
    return _exit_tool()


__all__ = ['restart_app', 'exit_app']
