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
from scripts.support.command_runner import (
    Step,
    add_common_args,
    python_script,
    run_steps,
)

CORE_GUI_STEPS = [
    Step(
        "required_dependencies_smoke",
        python_script("scripts/quality/check_required_dependencies.py", "--smoke-only"),
        timeout=120,
    ),
    Step("targeted", python_script("tests/smoke/targeted.py"), timeout=240),
    Step("ui_smoke", python_script("tests/smoke/ui.py"), timeout=120, use_xvfb=True),
    Step(
        "settings_ui_smoke",
        python_script("tests/smoke/settings_ui.py"),
        timeout=120,
        use_xvfb=True,
    ),
    Step(
        "theme_cycle_smoke",
        python_script("tests/smoke/theme_cycle.py"),
        timeout=120,
        use_xvfb=True,
    ),
    Step(
        "window_smoke",
        python_script("tests/smoke/windows.py"),
        timeout=120,
        use_xvfb=True,
    ),
    Step(
        "window_catalog_smoke",
        python_script("tests/smoke/window_catalog.py"),
        timeout=120,
        use_xvfb=True,
    ),
    Step(
        "toolbox_click_smoke",
        python_script("tests/smoke/toolbox_click.py"),
        timeout=120,
        use_xvfb=True,
    ),
    Step(
        "runtime_smoke",
        python_script("tests/smoke/runtime.py"),
        timeout=180,
        use_xvfb=True,
    ),
    Step(
        "e2e_flow_smoke",
        python_script("tests/e2e/main_flow.py"),
        timeout=180,
        use_xvfb=True,
    ),
    Step(
        "lifecycle_smoke",
        python_script("tests/smoke/lifecycle.py"),
        timeout=180,
        use_xvfb=True,
    ),
    Step(
        "deep_happy_path_smoke",
        python_script("tests/smoke/deep_happy_path.py"),
        timeout=240,
        use_xvfb=True,
    ),
]

FULL_RUNTIME_SMOKE_STEP = Step(
    "runtime_smoke_suite",
    python_script("scripts/manual/runtime_smoke_suite.py"),
    timeout=900,
)


def build_steps(*, full: bool) -> list[Step]:
    if full:
        return [FULL_RUNTIME_SMOKE_STEP]
    return list(CORE_GUI_STEPS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run GUI/Xvfb smoke checks separately from in-process unit/contract tests."
    )
    add_common_args(parser)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run scripts/manual/runtime_smoke_suite.py instead of the core GUI smoke subset.",
    )
    args = parser.parse_args(argv)
    code = run_steps(build_steps(full=args.full), dry_run=args.dry_run)
    if code == 0 and not args.dry_run:
        print("MANUAL_GUI_SMOKE_OK", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
