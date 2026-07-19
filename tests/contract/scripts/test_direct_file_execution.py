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


import subprocess
import sys
from pathlib import Path

from tests.support.paths import PROJECT_ROOT


DIRECT_BOOTSTRAP_MARKER = "# Direct file execution bootstrap"


def _python_files(base: Path) -> list[Path]:
    return sorted(
        path for path in base.rglob("*.py") if path.name != "__init__.py"
    )


def _run_direct(path: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )


def test_every_test_and_script_file_has_direct_execution_boundary() -> None:
    missing_bootstrap: list[str] = []
    missing_main: list[str] = []
    for base in (PROJECT_ROOT / "scripts", PROJECT_ROOT / "tests"):
        for path in _python_files(base):
            source = path.read_text(encoding="utf-8")
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            if DIRECT_BOOTSTRAP_MARKER not in source:
                missing_bootstrap.append(relative)
            if '__name__' not in source or '__main__' not in source:
                missing_main.append(relative)
    assert missing_bootstrap == []
    assert missing_main == []


def test_manual_runners_use_direct_file_paths() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((PROJECT_ROOT / "scripts/manual").glob("*.py"))
    )
    assert 'python_module("scripts.' not in sources
    assert "python_module('scripts." not in sources
    assert 'python_module("tests.' not in sources
    assert "python_module('tests." not in sources


def test_direct_script_execution_works_outside_repository(tmp_path: Path) -> None:
    result = _run_direct(
        PROJECT_ROOT / "scripts/manual/manual_unit_contracts.py",
        "--dry-run",
        cwd=tmp_path,
    )
    assert "scripts/arch_guard/main.py" in result.stdout
    assert "-m pytest -q --rootdir=. -c scripts/config/pytest.ini" in result.stdout


def test_direct_architecture_guard_execution_works_outside_repository(
    tmp_path: Path,
) -> None:
    result = _run_direct(
        PROJECT_ROOT / "scripts/arch_guard/main.py",
        "--help",
        cwd=tmp_path,
    )
    assert "architecture guard" in result.stdout.lower()


def test_direct_pytest_file_execution_works_outside_repository(tmp_path: Path) -> None:
    result = _run_direct(
        PROJECT_ROOT / "tests/unit/core/test_byte_size.py",
        cwd=tmp_path,
    )
    assert "2 passed" in result.stdout


def test_direct_support_module_execution_works_outside_repository(
    tmp_path: Path,
) -> None:
    result = _run_direct(
        PROJECT_ROOT / "scripts/arch_guard/current_rules.py",
        cwd=tmp_path,
    )
    assert "DIRECT_IMPORT_OK" in result.stdout


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
