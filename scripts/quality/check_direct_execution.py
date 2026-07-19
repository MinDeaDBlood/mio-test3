#!/usr/bin/env python3
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


import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIRECT_BOOTSTRAP_MARKER = "# Direct file execution bootstrap"


def _python_files(base: Path) -> list[Path]:
    return sorted(
        path for path in base.rglob("*.py") if path.name != "__init__.py"
    )


def _layout_issues() -> list[str]:
    issues: list[str] = []
    for base in (PROJECT_ROOT / "scripts", PROJECT_ROOT / "tests"):
        for path in _python_files(base):
            source = path.read_text(encoding="utf-8")
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            if DIRECT_BOOTSTRAP_MARKER not in source:
                issues.append(f"{relative}: direct execution bootstrap is missing")
            if '__name__' not in source or '__main__' not in source:
                issues.append(f"{relative}: direct execution entrypoint is missing")
    return issues


def _run(path: str, *args: str, cwd: Path) -> None:
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / path), *args],
        cwd=cwd,
        text=True,
        timeout=60,
        check=True,
    )


def _verify_samples() -> None:
    with tempfile.TemporaryDirectory(prefix="mio-direct-run-") as temp:
        cwd = Path(temp)
        _run("scripts/manual/manual_unit_contracts.py", "--dry-run", cwd=cwd)
        _run("scripts/arch_guard/main.py", "--help", cwd=cwd)
        _run("tests/unit/core/test_byte_size.py", cwd=cwd)
        _run("scripts/arch_guard/current_rules.py", cwd=cwd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate direct file execution for repository tests and scripts."
    )
    parser.add_argument(
        "--verify-samples",
        action="store_true",
        help="Launch representative scripts and tests from outside the repository.",
    )
    args = parser.parse_args(argv)

    issues = _layout_issues()
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    if args.verify_samples:
        _verify_samples()
    print("DIRECT_EXECUTION_LAYOUT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
