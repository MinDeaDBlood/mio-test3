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


import importlib.util
import os
import shutil
import subprocess
import sys

import pytest

from tests.support.paths import PROJECT_ROOT
PYTHON = sys.executable


def _require_gui_runtime_dependencies() -> None:
    missing = [
        package
        for package in ("sv_ttk",)
        if importlib.util.find_spec(package) is None
    ]
    if missing:
        pytest.skip(
            "GUI smoke dependencies are not installed: " + ", ".join(missing)
        )


def _run_script(relative_path: str, *, timeout: int = 90, use_xvfb: bool = False) -> subprocess.CompletedProcess[str]:
    parts = relative_path.split()
    if relative_path.startswith('-m '):
        cmd = [PYTHON, '-m', parts[1], *parts[2:]]
    else:
        cmd = [PYTHON, *parts]
    if use_xvfb:
        xvfb = shutil.which('xvfb-run')
        if not xvfb and not os.environ.get('DISPLAY'):
            pytest.skip('Tk display is not available and xvfb-run is not installed')
        if xvfb:
            cmd = ['env', '-u', 'DISPLAY', xvfb, '-a', *cmd]
    try:
        return subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b'').decode(errors='replace')
        return subprocess.CompletedProcess(cmd, 124, stdout, None)


def _assert_ok(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        'smoke script failed: '
        + ' '.join(map(str, result.args))
        + ('\n--- output ---\n' + result.stdout[-4000:] if result.stdout else '')
    )


@pytest.mark.external
@pytest.mark.smoke
def test_architecture_guard_script() -> None:
    _assert_ok(_run_script('-m scripts.arch_guard --quick', timeout=180))


@pytest.mark.smoke
def test_runtime_contracts_script() -> None:
    _assert_ok(_run_script('scripts/quality/check_runtime_contracts.py'))


@pytest.mark.smoke
def test_metric_baselines_script() -> None:
    _assert_ok(_run_script('scripts/quality/check_metric_baselines.py'))

@pytest.mark.smoke
def test_localization_keys_script() -> None:
    _assert_ok(_run_script('scripts/quality/check_localization_keys.py'))


@pytest.mark.external
@pytest.mark.smoke
def test_targeted_script() -> None:
    _assert_ok(_run_script('tests/smoke/targeted.py', timeout=240))


@pytest.mark.gui
@pytest.mark.smoke
def test_ui_smoke_script() -> None:
    _require_gui_runtime_dependencies()
    _assert_ok(_run_script('tests/smoke/ui.py', timeout=120, use_xvfb=True))


@pytest.mark.gui
@pytest.mark.smoke
def test_window_smoke_script() -> None:
    _require_gui_runtime_dependencies()
    _assert_ok(_run_script('tests/smoke/windows.py', timeout=120, use_xvfb=True))


@pytest.mark.gui
@pytest.mark.smoke
def test_byte_calculator_smoke_script() -> None:
    _require_gui_runtime_dependencies()
    _assert_ok(_run_script('tests/smoke/byte_calculator.py', timeout=120, use_xvfb=True))

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
