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
from collections.abc import Callable

from .current_rules import (
    check_app_ui_composition_boundary,
    check_ci_wrapper_exit_boundary,
    check_core_library_io_boundary,
    check_core_ownership,
    check_current_layer_dependencies,
    check_current_static_import_cycles,
    check_feature_separation,
    check_logic_ownership,
    check_no_base_exception_catches,
    check_removed_surfaces_stay_removed,
    check_runtime_ownership,
    check_ui_localization_boundary,
    check_ui_ownership,
)
from .reporting import FAIL, PASS, GuardContext, make_context
from .startup_rules import (
    check_bootstrap_import_surface,
    check_compileall,
    check_entrypoint_lazy_import_boundary,
    check_startup_smoke_imports,
)

Check = Callable[[GuardContext], None]


def _startup_checks() -> list[Check]:
    return [check_compileall, check_bootstrap_import_surface, check_entrypoint_lazy_import_boundary, check_startup_smoke_imports]


def _layer_checks() -> list[Check]:
    return [
        check_current_layer_dependencies,
        check_current_static_import_cycles,
        check_removed_surfaces_stay_removed,
        check_core_library_io_boundary,
        check_core_ownership,
        check_logic_ownership,
        check_no_base_exception_catches,
        check_app_ui_composition_boundary,
        check_feature_separation,
        check_ci_wrapper_exit_boundary,
    ]


def _runtime_checks() -> list[Check]:
    return [check_runtime_ownership]


def _ui_checks() -> list[Check]:
    return [check_ui_localization_boundary, check_ui_ownership]


SECTION_CHECKS: dict[str, list[Check]] = {
    'startup': _startup_checks(),
    'layers': _layer_checks(),
    'runtime': _runtime_checks(),
    'ui': _ui_checks(),
}
QUICK_SECTIONS = ('layers', 'runtime', 'ui')
FULL_SECTIONS = ('startup', 'layers', 'runtime', 'ui')


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run MIO-KITCHEN architecture guard checks.')
    parser.add_argument('--section', choices=tuple(SECTION_CHECKS), action='append', help='Run only the selected guard section. Can be passed multiple times.')
    parser.add_argument('--quick', action='store_true', help='Run all non-startup sections and skip compile/import smoke checks.')
    parser.add_argument('--no-compile', action='store_true', help='Skip compile inside the startup section.')
    return parser.parse_args(argv)


def _selected_sections(args: argparse.Namespace) -> tuple[str, ...]:
    if args.section:
        return tuple(dict.fromkeys(args.section))
    if args.quick:
        return QUICK_SECTIONS
    return FULL_SECTIONS


def _run_checks(ctx: GuardContext, checks: list[Check], *, no_compile: bool) -> None:
    for check in checks:
        if no_compile and check is check_compileall:
            print('\n-- Compile syntax check --')
            print(f'  {PASS} Skipped by --no-compile')
            continue
        check(ctx)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    ctx = make_context()
    sections = _selected_sections(args)
    print('=' * 60)
    print('  MIO-KITCHEN Architecture Guard')
    print('=' * 60)
    print('  Sections: ' + ', '.join(sections))
    for section in sections:
        _run_checks(ctx, SECTION_CHECKS[section], no_compile=args.no_compile)
    print('\n' + '=' * 60)
    if ctx.violations:
        print(f'  {FAIL} {len(ctx.violations)} violation(s) found')
        print('=' * 60)
        return 1
    print(f'  {PASS} All checks passed')
    print('=' * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
