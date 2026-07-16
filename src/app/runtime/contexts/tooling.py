from __future__ import annotations

from src.app.runtime.defaults_access import require_tool_log, require_tool_self


def resolve_tool_self(tool_self: str | None = None) -> str:
    if tool_self is not None:
        return str(tool_self)
    return require_tool_self()


def resolve_tool_log(tool_log: str | None = None) -> str:
    if tool_log is not None:
        return str(tool_log)
    return require_tool_log()


__all__ = ["resolve_tool_log", "resolve_tool_self"]
