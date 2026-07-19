from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import logging

from src.app.ui_scheduler import AppUiScheduler


def test_scheduler_logs_callback_failure_and_continues(caplog, monkeypatch) -> None:
    scheduler = AppUiScheduler(host_window=None)
    completed: list[str] = []

    def broken_callback() -> None:
        raise RuntimeError("callback failure")

    def next_callback() -> None:
        completed.append("next")

    scheduler._queue.put((broken_callback, ()))
    scheduler._queue.put((next_callback, ()))
    monkeypatch.setattr(scheduler, "_schedule_next", lambda: True)

    with caplog.at_level(logging.ERROR, logger="src.app.ui_scheduler"):
        scheduler._drain()

    assert completed == ["next"]
    assert "AppUiScheduler callback failed" in caplog.text
    assert "RuntimeError: callback failure" in caplog.text


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
