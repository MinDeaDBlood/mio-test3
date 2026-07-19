from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / 'src').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'tests').is_dir()
        and (_DIRECT_PROJECT_ROOT / 'scripts').is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f'Project root was not found for {__file__}')

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ''}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix('')
    __package__ = '.'.join(_direct_relative.parts[:-1])


from weakref import WeakSet

import pytest

import src.ui.common.window_appearance as appearance


class _FakeWindow:
    def __init__(self) -> None:
        self.alpha = 1.0
        self.background = ''
        self.bindings: dict[str, object] = {}
        self.exists = True

    def winfo_exists(self) -> int:
        return int(self.exists)

    def attributes(self, *args: object) -> object:
        if len(args) == 2 and args[0] == '-alpha':
            self.alpha = float(args[1])
            return None
        if args == ('-alpha',):
            return self.alpha
        return None

    def configure(self, **kwargs: object) -> object:
        if 'background' in kwargs:
            self.background = str(kwargs['background'])
        return None

    def bind(self, sequence: str, func: object, add: str | None = None) -> object:
        del add
        self.bindings[sequence] = func
        return sequence


@pytest.fixture(autouse=True)
def _reset_window_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(appearance, '_WINDOWS', WeakSet())
    monkeypatch.setattr(appearance, '_THEME_ID', 'dark')
    monkeypatch.setattr(appearance, '_WINDOW_ALPHA', 1.0)
    monkeypatch.setattr(appearance, 'set_title_bar_color', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(appearance, 'apply_native_theme', lambda *_args, **_kwargs: None)


def test_transparency_alpha_is_clamped() -> None:
    assert appearance.normalize_window_alpha('0.80') == 0.8
    assert appearance.normalize_window_alpha('0.10') == 0.55
    assert appearance.normalize_window_alpha('2.0') == 1.0
    assert appearance.normalize_window_alpha('bad') == 0.9


def test_registered_window_receives_theme_and_transparency() -> None:
    window = _FakeWindow()
    appearance.register_window(window)
    assert window.background == '#1c1c1c'
    assert window.alpha == 1.0
    assert window.bindings == {}

    appearance.apply_transparency_to_windows(enabled=True, effect_alpha='0.82')
    assert window.alpha == 0.82

    appearance.apply_theme_to_windows('light')
    assert window.background == '#fafafa'


def test_registration_is_idempotent_and_new_window_inherits_state() -> None:
    first = _FakeWindow()
    appearance.register_window(first)
    appearance.register_window(first)
    assert first.bindings == {}

    appearance.apply_transparency_to_windows(enabled=True, effect_alpha=0.75)
    second = _FakeWindow()
    appearance.register_window(second)
    assert second.alpha == 0.75


def test_registration_does_not_install_post_map_restyle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[bool] = []
    original = appearance._apply_to_window

    def record(window: object, *, include_widget_tree: bool = True) -> None:
        calls.append(include_widget_tree)
        original(window, include_widget_tree=include_widget_tree)

    monkeypatch.setattr(appearance, '_apply_to_window', record)
    window = _FakeWindow()
    appearance.register_window(window)

    assert calls == [True]
    assert window.bindings == {}


def test_background_is_applied_before_native_titlebar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    window = _FakeWindow()
    original_configure = window.configure
    original_attributes = window.attributes

    def configure(**kwargs: object) -> object:
        events.append('background')
        return original_configure(**kwargs)

    def attributes(*args: object) -> object:
        if len(args) == 2:
            events.append('alpha')
        return original_attributes(*args)

    window.configure = configure  # type: ignore[method-assign]
    window.attributes = attributes  # type: ignore[method-assign]
    monkeypatch.setattr(
        appearance,
        'apply_native_theme',
        lambda *_args, **_kwargs: events.append('widgets'),
    )
    monkeypatch.setattr(
        appearance,
        'set_title_bar_color',
        lambda *_args, **_kwargs: events.append('titlebar'),
    )

    appearance.register_window(window)

    assert events == ['background', 'alpha', 'widgets', 'titlebar']


def test_destroyed_window_race_does_not_escape_tk_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = _FakeWindow()
    appearance.register_window(window)
    window.exists = False
    appearance.apply_theme_to_windows('light')


def test_theme_and_transparency_updates_do_not_break_active_alpha_gate() -> None:
    window = _FakeWindow()
    appearance.register_window(window)
    window.alpha = 0.0
    window._appearance_alpha_gated = True

    appearance.apply_theme_to_windows('light')
    appearance.apply_transparency_to_windows(enabled=True, effect_alpha=0.72)

    assert window.background == '#fafafa'
    assert window.alpha == 0.0

    window._appearance_alpha_gated = False
    appearance.apply_transparency_to_windows(enabled=True, effect_alpha=0.72)
    assert window.alpha == 0.72


if __name__ == '__main__':
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
