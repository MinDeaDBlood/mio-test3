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


from types import SimpleNamespace

import src.app.bootstrap as bootstrap
import src.app.composition.welcome as welcome_composition


class _Splash:
    def __init__(self, events: list[str]) -> None:
        self._events = events

    def close(self, *, reveal_main: bool = True) -> None:
        self._events.append(f"splash.close:{reveal_main}")


def test_welcome_closes_splash_before_waiting_for_modal_ui(monkeypatch) -> None:
    events: list[str] = []
    splash = _Splash(events)

    monkeypatch.setattr(
        bootstrap,
        "require_settings",
        lambda: SimpleNamespace(oobe="0"),
    )
    monkeypatch.setattr(
        bootstrap,
        "stop_startup_watchdog",
        lambda: events.append("watchdog.stop"),
    )
    monkeypatch.setattr(
        bootstrap,
        "start_startup_watchdog",
        lambda: events.append("watchdog.start"),
    )
    monkeypatch.setattr(
        bootstrap,
        "log_startup_phase",
        lambda phase, **_details: events.append(f"phase:{phase}"),
    )
    monkeypatch.setattr(
        welcome_composition,
        "open_welcome",
        lambda: events.append("welcome.open"),
    )

    remaining_splash = bootstrap._show_welcome_if_needed(splash)

    assert remaining_splash is None
    assert events == [
        "splash.close:False",
        "phase:application startup splash closed before welcome wizard",
        "watchdog.stop",
        "phase:welcome wizard opened",
        "welcome.open",
        "phase:welcome wizard closed",
        "watchdog.start",
    ]


def test_completed_oobe_keeps_splash_until_normal_startup_finishes(monkeypatch) -> None:
    splash = object()
    monkeypatch.setattr(
        bootstrap,
        "require_settings",
        lambda: SimpleNamespace(oobe="5"),
    )

    assert bootstrap._show_welcome_if_needed(splash) is splash


def test_modal_watchdog_is_rearmed_when_welcome_raises(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(
        bootstrap,
        "stop_startup_watchdog",
        lambda: events.append("watchdog.stop"),
    )
    monkeypatch.setattr(
        bootstrap,
        "start_startup_watchdog",
        lambda: events.append("watchdog.start"),
    )
    monkeypatch.setattr(
        bootstrap,
        "log_startup_phase",
        lambda phase, **_details: events.append(f"phase:{phase}"),
    )

    def fail() -> None:
        events.append("callback")
        raise RuntimeError("welcome failed")

    try:
        bootstrap._run_startup_modal_interaction(
            name="welcome wizard",
            callback=fail,
        )
    except RuntimeError as exc:
        assert str(exc) == "welcome failed"
    else:
        raise AssertionError("RuntimeError was not propagated")

    assert events == [
        "watchdog.stop",
        "phase:welcome wizard opened",
        "callback",
        "phase:welcome wizard closed",
        "watchdog.start",
    ]


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
