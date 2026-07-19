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


import os

import pytest

import src.ui.common.window_appearance as appearance
import src.ui.common.window_reveal as window_reveal


class _RevealWindow:
    def __init__(self) -> None:
        self.exists = True
        self.alpha = 1.0
        self._appearance_alpha_gated = False
        self.events: list[str] = []
        self.idle_callbacks: list[object] = []
        self.timer_callbacks: list[tuple[int, object]] = []
        self.cancelled_callbacks: list[object] = []

    def winfo_exists(self) -> int:
        return int(self.exists)

    def attributes(self, *args: object) -> object:
        if len(args) == 2 and args[0] == '-alpha':
            self.alpha = float(args[1])
            self.events.append(f'alpha:{self.alpha}')
        return None

    def deiconify(self) -> None:
        self.events.append('deiconify')

    def lift(self) -> None:
        self.events.append('lift')

    def focus_force(self) -> None:
        self.events.append('focus')

    def focus_set(self) -> None:
        self.events.append('focus-fallback')

    def update(self) -> None:
        self.events.append('paint')

    def update_idletasks(self) -> None:
        self.events.append('idle-paint')

    def after_idle(self, callback: object) -> str:
        self.idle_callbacks.append(callback)
        return f'idle-{len(self.idle_callbacks)}'

    def after(self, delay: int, callback: object) -> str:
        self.timer_callbacks.append((delay, callback))
        return f'timer-{len(self.timer_callbacks)}'

    def after_cancel(self, callback_id: object) -> None:
        self.cancelled_callbacks.append(callback_id)


@pytest.fixture
def reveal_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    if os.name != 'nt':
        pytest.skip('Windows alpha-gated reveal is only available on Windows')
    monkeypatch.setattr(
        window_reveal,
        'paint_window_now',
        lambda window, **_kwargs: window.events.append('paint') or True,
    )


def test_stale_root_reveal_callback_cannot_remove_newer_alpha_gate(
    reveal_runtime: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del reveal_runtime
    window = _RevealWindow()
    def resolve_alpha() -> float:
        return 0.72
    monkeypatch.setattr(appearance, 'current_window_alpha', resolve_alpha)
    monkeypatch.setattr(window_reveal, 'current_window_alpha', resolve_alpha)

    window._mio_reveal_generation = 2
    window._appearance_alpha_gated = True
    window.alpha = 0.0
    window_reveal._restore_alpha_gate(window, 1, 0.81)
    assert window.alpha == 0.0
    assert window._appearance_alpha_gated is True

    window_reveal._restore_alpha_gate(window, 2, 0.72)

    assert window.alpha == 0.72
    assert window._appearance_alpha_gated is False


def test_root_reveal_restores_latest_global_window_alpha(
    reveal_runtime: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del reveal_runtime
    window = _RevealWindow()
    latest_alpha = [0.88]
    def resolve_alpha() -> float:
        return latest_alpha[0]
    monkeypatch.setattr(appearance, 'current_window_alpha', resolve_alpha)
    monkeypatch.setattr(
        window_reveal,
        'current_window_alpha',
        resolve_alpha,
        raising=False,
    )

    def paint_and_change_alpha(window: _RevealWindow, **_kwargs: object) -> bool:
        window.events.append('paint')
        latest_alpha[0] = 0.64
        return True

    monkeypatch.setattr(window_reveal, 'paint_window_now', paint_and_change_alpha)
    window_reveal.reveal_window_after_layout(window, target_alpha=0.91)

    assert window.alpha == 0.64
    assert window._appearance_alpha_gated is False


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
