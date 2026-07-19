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
    _direct_relative = (
        _DirectPath(__file__)
        .resolve()
        .relative_to(_DIRECT_PROJECT_ROOT)
        .with_suffix("")
    )
    __package__ = ".".join(_direct_relative.parts[:-1])


import argparse

from pathlib import Path


from scripts.support.command_runner import (
    Step,
    add_common_args,
    python_module,
    python_script,
    run_steps,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_steps() -> list[Step]:
    pytest_environment = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    return [
        Step(
            "test_integrity",
            python_script("scripts/quality/check_test_integrity.py"),
            timeout=60,
        ),
        Step(
            "pytest_all",
            python_module(
                "pytest",
                "-q",
                "--rootdir=.",
                "-c",
                "scripts/config/pytest.ini",
                "tests",
            ),
            timeout=600,
            env=pytest_environment,
        ),
        Step(
            "direct_execution",
            python_script("scripts/quality/check_direct_execution.py"),
            timeout=180,
        ),
        Step(
            "typed_boundaries",
            python_script("scripts/quality/check_typed_boundaries.py"),
            timeout=240,
        ),
        Step(
            "ruff",
            python_module("ruff", "check", ".", "--config", "ruff.toml"),
            timeout=180,
        ),
        Step(
            "architecture_guard",
            python_script("scripts/arch_guard/main.py"),
            timeout=240,
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Architecture Guard and the complete pytest suite. External GUI smoke scripts stay in the separate runtime smoke contour."
    )
    add_common_args(parser)
    args = parser.parse_args(argv)
    code = run_steps(build_steps(), dry_run=args.dry_run)
    if code == 0 and not args.dry_run:
        print("MANUAL_UNIT_CONTRACTS_OK", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
