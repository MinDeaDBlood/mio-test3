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
    _direct_relative = (
        _DirectPath(__file__)
        .resolve()
        .relative_to(_DIRECT_PROJECT_ROOT)
        .with_suffix("")
    )
    __package__ = ".".join(_direct_relative.parts[:-1])

import pytest

import src.ui.common.windowing as windowing


class _FakeTk:
    def __init__(self, window: "_FakeWindow") -> None:
        self.window = window

    def call(self, *args: object) -> str:
        assert args[:2] == ("wm", "state")
        return "normal" if self.window.visible else "withdrawn"


class _FakeWindow:
    def __init__(self, *, visible: bool = True, top: object | None = None) -> None:
        self.visible = visible
        self.tk = _FakeTk(self)
        self._w = ".fake"
        self.top = top or self
        self.exists = True
        self.focused: object | None = None
        self.transient_owner: object | None = None
        self.lift_count = 0
        self.focus_force_count = 0
        self.topmost_values: list[bool] = []
        self.after_callbacks: list[tuple[int, object]] = []

    def winfo_exists(self) -> int:
        return int(self.exists)

    def winfo_toplevel(self) -> object:
        return self.top

    def state(self) -> str:
        return "normal" if self.visible else "withdrawn"

    def focus_get(self) -> object | None:
        return self.focused

    def transient(self, owner: object) -> None:
        self.transient_owner = owner

    def lift(self) -> None:
        self.lift_count += 1

    def focus_force(self) -> None:
        self.focus_force_count += 1

    def attributes(self, name: str, value: bool) -> None:
        assert name == "-topmost"
        self.topmost_values.append(value)

    def after(self, delay: int, callback: object) -> None:
        self.after_callbacks.append((delay, callback))


def test_window_state_model_does_not_shadow_native_visibility_query() -> None:
    window = _FakeWindow()
    window.state = object()

    assert windowing._window_is_visible(window) is True

    window.visible = False
    assert windowing._window_is_visible(window) is False


def test_explicit_widget_resolves_to_its_toplevel() -> None:
    owner = _FakeWindow()
    child_widget = _FakeWindow(top=owner)

    assert windowing.resolve_window_owner(child_widget) is owner


def test_registered_root_uses_focused_application_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _FakeWindow()
    focused_owner = _FakeWindow()
    root.focused = _FakeWindow(top=focused_owner)
    monkeypatch.setattr(windowing, "_MAIN_WINDOW", None)
    windowing.register_main_window(root)

    assert windowing.resolve_window_owner() is focused_owner


def test_visible_window_is_owned_raised_and_focused() -> None:
    owner = _FakeWindow()
    window = _FakeWindow()

    windowing.present_window(window, owner=owner, transient=True)

    assert window.transient_owner is owner
    assert window.lift_count == 1
    assert window.focus_force_count == 1
    assert window.topmost_values == []
    assert window.after_callbacks == []


def test_regular_tool_window_is_focused_without_becoming_transient() -> None:
    owner = _FakeWindow()
    window = _FakeWindow()

    windowing.present_window(window, owner=owner)

    assert window.transient_owner is None
    assert window.lift_count == 1
    assert window.focus_force_count == 1


def test_withdrawn_window_is_not_forced_to_front() -> None:
    owner = _FakeWindow()
    window = _FakeWindow(visible=False)

    windowing.present_window(window, owner=owner, transient=True)

    assert window.transient_owner is None
    assert window.lift_count == 0
    assert window.focus_force_count == 0
    assert window.topmost_values == []


class _MapEvent:
    def __init__(self, widget: object) -> None:
        self.widget = widget


def test_descendant_map_event_does_not_present_toplevel() -> None:
    window = object.__new__(windowing.Toplevel)
    window._focus_on_open = True
    window._foreground_scheduled = False
    window._foreground_presented = False
    scheduled: list[bool] = []
    window.after_idle = lambda callback: scheduled.append(True)

    window._on_window_mapped(_MapEvent(object()))

    assert scheduled == []


def test_toplevel_map_event_schedules_only_once() -> None:
    window = object.__new__(windowing.Toplevel)
    window._initial_show_complete = True
    window._focus_on_open = True
    window._foreground_scheduled = False
    window._foreground_presented = False
    callbacks: list[tuple[int, object]] = []
    window.after = lambda delay, callback: callbacks.append((delay, callback))

    event = _MapEvent(window)
    window._on_window_mapped(event)
    window._on_window_mapped(event)

    assert len(callbacks) == 1
    assert callbacks[0][0] == 0


def test_toplevel_does_not_reschedule_after_successful_presentation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = object.__new__(windowing.Toplevel)
    window._focus_on_open = True
    window._foreground_scheduled = True
    window._foreground_presented = False
    window._window_owner = None
    window._transient_owner_enabled = False
    window._initial_show_complete = True
    callbacks: list[tuple[int, object]] = []
    window.after = lambda delay, callback: callbacks.append((delay, callback))
    monkeypatch.setattr(windowing, "present_window", lambda *_args, **_kwargs: True)

    window._present_scheduled_window()
    window._on_window_mapped(_MapEvent(window))

    assert window._foreground_presented is True
    assert callbacks == []


def test_initial_show_themes_and_centers_before_deiconifying(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(windowing.os, 'name', 'nt')
    window = object.__new__(windowing.Toplevel)
    window._initial_show_scheduled = True
    window._initial_show_in_progress = False
    window._initial_reveal_scheduled = False
    window._initial_show_complete = False
    window._initial_show_generation = 0
    window._center_on_open = True
    window._centered_once = False
    window._focus_on_open = True
    window.winfo_exists = lambda: 1
    events: list[str] = []
    idle_callbacks: list[object] = []
    timer_callbacks: list[tuple[int, object]] = []
    monkeypatch.setattr(
        windowing,
        'register_window',
        lambda _window: events.append('theme'),
    )
    window.center_on_screen = lambda **_kwargs: events.append('center')
    window.attributes = lambda _name, value: events.append(f'alpha:{value}')
    monkeypatch.setattr(
        windowing,
        'paint_window_now',
        lambda _window, **_kwargs: events.append('paint') or True,
    )
    window.after_idle = lambda callback: idle_callbacks.append(callback)
    window.after = lambda delay, callback: timer_callbacks.append((delay, callback))
    window.present_in_foreground = lambda **_kwargs: events.append('present')
    monkeypatch.setattr(
        windowing.TkToplevel,
        'deiconify',
        lambda _window: events.append('deiconify'),
    )
    monkeypatch.setattr(windowing, 'current_window_alpha', lambda: 0.87)
    monkeypatch.setattr(
        windowing,
        '_flush_desktop_compositor',
        lambda: events.append('flush'),
    )

    window._show_when_ready()

    assert events == [
        'theme',
        'center',
        'alpha:0.0',
        'deiconify',
        'paint',
        'present',
        'alpha:0.87',
        'flush',
    ]
    assert window._initial_show_scheduled is False
    assert window._initial_show_complete is True
    assert idle_callbacks == []
    assert timer_callbacks == []


def test_destroy_during_hidden_first_paint_clears_initial_show_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(windowing.os, 'name', 'nt')
    window = object.__new__(windowing.Toplevel)
    window._initial_show_scheduled = True
    window._initial_show_in_progress = False
    window._initial_reveal_scheduled = False
    window._initial_show_complete = False
    window._initial_show_generation = 0
    window._center_on_open = False
    window._centered_once = False
    window._focus_on_open = True
    window._appearance_alpha_gated = False
    exists = [True]
    idle_callbacks: list[object] = []

    window.winfo_exists = lambda: int(exists[0])
    window.attributes = lambda *_args: None
    monkeypatch.setattr(
        windowing,
        'paint_window_now',
        lambda _window, **_kwargs: exists.__setitem__(0, False) or False,
    )
    window.after_idle = lambda callback: idle_callbacks.append(callback)
    window.after = lambda *_args: None
    monkeypatch.setattr(windowing, 'register_window', lambda _window: None)
    monkeypatch.setattr(windowing.TkToplevel, 'deiconify', lambda _window: None)
    monkeypatch.setattr(windowing.TkToplevel, 'withdraw', lambda _window: None)

    window._show_when_ready()

    assert window._initial_show_in_progress is False
    assert window._initial_reveal_scheduled is False
    assert window._appearance_alpha_gated is False
    assert idle_callbacks == []


def test_tclerror_during_hidden_first_paint_does_not_wedge_initial_show(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(windowing.os, 'name', 'nt')
    window = object.__new__(windowing.Toplevel)
    window._initial_show_scheduled = True
    window._initial_show_in_progress = False
    window._initial_reveal_scheduled = False
    window._initial_show_complete = False
    window._initial_show_generation = 0
    window._center_on_open = False
    window._centered_once = False
    window._focus_on_open = True
    window._appearance_alpha_gated = False
    alpha_values: list[float] = []

    window.winfo_exists = lambda: 1
    window.attributes = lambda _name, value: alpha_values.append(float(value))

    def fail_paint(_window: object, **_kwargs: object) -> bool:
        raise windowing.TclError('paint failed')

    monkeypatch.setattr(windowing, 'paint_window_now', fail_paint)
    window.after_idle = lambda _callback: None
    window.after = lambda *_args: None
    monkeypatch.setattr(windowing, 'register_window', lambda _window: None)
    monkeypatch.setattr(windowing.TkToplevel, 'deiconify', lambda _window: None)
    monkeypatch.setattr(windowing.TkToplevel, 'withdraw', lambda _window: None)
    monkeypatch.setattr(windowing, 'current_window_alpha', lambda: 0.73)

    window._show_when_ready()

    assert alpha_values[0] == 0.0
    assert window._initial_show_in_progress is False
    assert window._initial_reveal_scheduled is False
    assert window._appearance_alpha_gated is False


def test_explicit_master_becomes_transient_before_first_native_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(windowing.os, 'name', 'nt')
    window = object.__new__(windowing.Toplevel)
    owner = _FakeWindow()
    window._initial_show_scheduled = True
    window._initial_show_in_progress = False
    window._initial_reveal_scheduled = False
    window._initial_show_complete = False
    window._initial_show_generation = 0
    window._center_on_open = False
    window._centered_once = False
    window._focus_on_open = True
    window._foreground_presented = False
    window._window_owner = owner
    window._transient_owner_enabled = True
    window.winfo_exists = lambda: 1
    events: list[str] = []
    idle_callbacks: list[object] = []
    timer_callbacks: list[tuple[int, object]] = []
    presentation: list[tuple[object | None, bool]] = []
    window.transient = lambda _owner: events.append('transient-owner')

    monkeypatch.setattr(windowing, 'register_window', lambda _window: None)
    monkeypatch.setattr(
        windowing.TkToplevel,
        'deiconify',
        lambda _window: events.append('deiconify'),
    )
    monkeypatch.setattr(windowing, 'current_window_alpha', lambda: 0.84)
    monkeypatch.setattr(
        windowing,
        '_flush_desktop_compositor',
        lambda: events.append('flush'),
    )

    def present(_window, *, owner=None, transient=False) -> bool:
        presentation.append((owner, transient))
        events.append('present')
        return True

    monkeypatch.setattr(windowing, 'present_window', present)
    window.attributes = lambda _name, value: events.append(f'alpha:{value}')
    monkeypatch.setattr(
        windowing,
        'paint_window_now',
        lambda _window, **_kwargs: events.append('paint') or True,
    )
    window.after_idle = lambda callback: idle_callbacks.append(callback)
    window.after = lambda delay, callback: timer_callbacks.append((delay, callback))

    window._show_when_ready()

    assert presentation == [(owner, False)]
    assert events.index('transient-owner') < events.index('deiconify')
    assert events.index('paint') < events.index('present')
    assert events.index('present') < events.index('alpha:0.84')
    assert idle_callbacks == []
    assert timer_callbacks == []


def test_manual_first_deiconify_uses_the_same_gate_synchronously() -> None:
    window = object.__new__(windowing.Toplevel)
    window._auto_show = False
    window._initial_show_complete = False
    window._initial_show_in_progress = False
    window._initial_show_generation = 0
    events: list[str] = []

    def begin() -> None:
        events.append('begin')
        window._initial_show_in_progress = True

    def finish(_generation: int | None = None) -> None:
        events.append('finish')
        window._initial_show_in_progress = False
        window._initial_show_complete = True

    window._show_when_ready = begin
    window._finish_initial_show = finish

    window.deiconify()

    assert events == ['begin', 'finish']
    assert window._initial_show_complete is True


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
