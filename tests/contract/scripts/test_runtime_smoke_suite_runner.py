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
import sys

import pytest

from scripts.manual import runtime_smoke_suite as suite
from scripts.support.command_runner import Step, run_steps


def test_runtime_smoke_suite_dry_run_validates_real_inventory(capsys) -> None:
    assert suite.main(["--dry-run"]) == 0

    output = capsys.readouterr().out
    assert "RUNTIME_SMOKE_SUITE_DRY_RUN_OK" in output
    assert "MISSING:" not in output
    for label, command in suite.TESTS:
        assert f"==> {label}:" in output
        assert command[0] == suite.sys.executable
        for argument in command[1:]:
            if argument.endswith(".py"):
                assert (suite.PROJECT_ROOT / argument).is_file()


@pytest.mark.skipif(os.name != "nt", reason="native desktop branch is Windows-only")
def test_runtime_smoke_suite_uses_the_real_windows_desktop() -> None:
    base_env = os.environ.copy()
    process, env, error_log = suite._start_xvfb_environment(base_env)

    assert process is None
    assert env is base_env
    assert error_log is None


def test_command_runner_uses_utf8_for_python_child_output(
    capsys,
    tmp_path,
) -> None:
    step = Step(
        "unicode_output",
        [sys.executable, "-c", "print('Русский текст — UTF-8')"],
    )

    assert run_steps([step], cwd=tmp_path) == 0

    output = capsys.readouterr().out
    assert "Русский текст — UTF-8" in output


def test_command_runner_does_not_crash_on_non_utf8_native_output(
    capsys,
    tmp_path,
) -> None:
    step = Step(
        "native_bytes",
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(bytes.fromhex('fffe'))",
        ],
    )

    assert run_steps([step], cwd=tmp_path) == 0
    assert "native_bytes" in capsys.readouterr().out


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
