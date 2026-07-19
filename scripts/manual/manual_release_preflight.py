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
import sys
from pathlib import Path


from scripts.support.command_runner import Step, add_common_args, python_script, run_steps

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MAX_WARNING_ISSUES = 15
DEFAULT_MAX_MISSING_KEYS_PER_LANGUAGE = 165


def build_steps(*, skip_install: bool, max_warning_issues: int, max_missing_keys_per_language: int) -> list[Step]:
    steps: list[Step] = []
    if not skip_install:
        steps.append(Step('system_dependencies', python_script('scripts/quality/check_system_dependencies.py'), timeout=30))
        steps.append(
            Step(
                'install_release_dependencies',
                [
                    sys.executable,
                    '-m',
                    'pip',
                    'install',
                    '-r',
                    'requirements.txt',
                ],
                timeout=900,
            )
        )
    steps.extend(
        [
            Step('required_dependencies_smoke', python_script('scripts/quality/check_required_dependencies.py', '--smoke-only'), timeout=120),
            Step(
                'localization_keys',
                python_script(
                    'scripts/quality/check_localization_keys.py',
                    '--max-warning-issues',
                    str(max_warning_issues),
                    '--max-missing-keys-per-language',
                    str(max_missing_keys_per_language),
                ),
                timeout=60,
            ),
        ]
    )
    return steps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run strict release preflight: validate known OS prerequisites, install dependencies, then validate runtime dependencies and localization policy.')
    add_common_args(parser)
    parser.add_argument('--skip-install', action='store_true', help='Prepared-environment mode: skip OS prerequisite and pip install steps. Python runtime dependencies must already be installed; required dependency checks still run and may fail in a clean environment.')
    parser.add_argument('--max-warning-issues', type=int, default=DEFAULT_MAX_WARNING_ISSUES)
    parser.add_argument('--max-missing-keys-per-language', type=int, default=DEFAULT_MAX_MISSING_KEYS_PER_LANGUAGE)
    args = parser.parse_args(argv)
    code = run_steps(
        build_steps(
            skip_install=args.skip_install,
            max_warning_issues=args.max_warning_issues,
            max_missing_keys_per_language=args.max_missing_keys_per_language,
        ),
        dry_run=args.dry_run,
    )
    if code == 0 and not args.dry_run:
        print('MANUAL_RELEASE_PREFLIGHT_OK', flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
