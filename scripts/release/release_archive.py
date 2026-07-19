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
import tempfile
from pathlib import Path


from scripts.support.command_runner import (
    Step,
    add_common_args,
    python_script,
    run_steps,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_steps(*, output: Path, skip_checks: bool) -> list[Step]:
    command: list[str] = []
    if skip_checks:
        command.append("--skip-checks")
    command.extend(["--output", str(output)])
    return [
        Step(
            "release_archive",
            python_script("scripts/release/build_release_archive.py", *command),
            timeout=180,
        )
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Package an existing dist directory and validate archive/manifest generation in its own CI contour."
    )
    add_common_args(parser)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Release ZIP output. Defaults to a temp path for CI.",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip build_release_archive.py preflight checks when a prior CI job already ran them.",
    )
    args = parser.parse_args(argv)
    output = args.output or Path(tempfile.gettempdir()) / "mio_ci_release_archive.zip"
    code = run_steps(
        build_steps(output=output, skip_checks=args.skip_checks), dry_run=args.dry_run
    )
    if code == 0 and not args.dry_run:
        print(f"RELEASE_ARCHIVE_OK: {output}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
