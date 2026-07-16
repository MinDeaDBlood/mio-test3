from __future__ import annotations


from src.app.bug_report.controller import BugReportApplicationContext
from src.app.runtime.contexts.settings import resolve_settings, resolve_states
from src.app.runtime.contexts.tooling import resolve_tool_log
from src.core.random_utils import v_code


def snapshot_settings(settings: object) -> dict[str, str]:
    """Capture public scalar settings without leaking the live repository object into logic."""
    values: dict[str, str] = {}
    for name, raw_value in vars(settings).items():
        if name.startswith("_") or name == "config" or callable(raw_value):
            continue
        if hasattr(raw_value, "get"):
            try:
                raw_value = raw_value.get()
            except Exception:
                continue
        if isinstance(raw_value, (str, int, float, bool)) or raw_value is None:
            values[name] = "" if raw_value is None else str(raw_value)
    return dict(sorted(values.items()))


def build_bug_report_runtime_context() -> BugReportApplicationContext:
    settings = resolve_settings()
    states = resolve_states()
    run_source = states.run_source
    if hasattr(run_source, "get"):
        run_source = run_source.get()
    return BugReportApplicationContext(
        tool_log=resolve_tool_log(),
        version_code=v_code(),
        tool_version=str(settings.version),
        run_source=str(run_source),
        settings=snapshot_settings(settings),
    )


__all__ = ["build_bug_report_runtime_context", "snapshot_settings"]
