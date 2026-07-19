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
import stat
from pathlib import Path

import pytest

from src.platform import startup
from src.platform.startup import prepare_tool_binaries


@pytest.mark.skipif(os.name != "posix", reason="POSIX execute bits are unavailable")
def test_prepare_tool_binaries_adds_execute_bits_on_posix(tmp_path: Path) -> None:
    binary = tmp_path / "magiskboot"
    binary.write_bytes(b"fake")
    binary.chmod(0o644)

    prepare_tool_binaries(tmp_path)

    mode = stat.S_IMODE(binary.stat().st_mode)
    assert mode & 0o111 == 0o111


def test_prepare_tool_binaries_is_noop_on_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary = tmp_path / "magiskboot.exe"
    binary.write_bytes(b"fake")
    chmod_calls: list[tuple[Path, int]] = []

    monkeypatch.setattr(startup.os, "name", "nt")
    monkeypatch.setattr(
        Path,
        "chmod",
        lambda self, mode: chmod_calls.append((self, mode)),
    )

    prepare_tool_binaries(tmp_path)

    assert chmod_calls == []
if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
