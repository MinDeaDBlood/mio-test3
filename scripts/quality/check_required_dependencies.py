"""Runtime/release dependency preflight for MIO-KITCHEN.

The checker is intentionally independent from ``src`` so it can run before the
application bootstrap. It validates importability, package versions and a few
namespace-package pitfalls that can otherwise surface only during GUI smoke
flows.
"""

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
import importlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Iterable


@dataclass(frozen=True)
class DependencySpec:
    import_name: str
    distribution: str | None
    category: str
    required: bool = True
    note: str = ''
    platforms: tuple[str, ...] = ()


@dataclass(frozen=True)
class DependencyStatus:
    import_name: str
    distribution: str | None
    category: str
    required: bool
    ok: bool
    version: str | None
    error: str | None
    note: str = ''


DEPENDENCIES: tuple[DependencySpec, ...] = (
    DependencySpec('tkinter', None, 'ui', True, 'Tk runtime required for desktop GUI smoke.'),
    DependencySpec('PIL', 'Pillow', 'runtime', True, 'Image handling dependency.'),
    DependencySpec('requests', 'requests', 'runtime', True, 'Repository/network dependency.'),
    DependencySpec('google.protobuf', 'protobuf', 'runtime', True, 'Payload manifest parser dependency.'),
    DependencySpec('Crypto', 'pycryptodome', 'runtime', True, 'Crypto namespace provided by pycryptodome.'),
    DependencySpec('zstandard', 'zstandard', 'runtime', True, 'Zstandard image/archive support.'),
    DependencySpec('lxml', 'lxml', 'runtime', True, 'XML parsing dependency.'),
    DependencySpec('cryptography', 'cryptography', 'runtime', True, 'Crypto helper dependency.'),
    DependencySpec('httpx', 'httpx', 'runtime', True, 'HTTP client dependency.'),
    DependencySpec('toml', 'toml', 'runtime', True, 'TOML config/parser dependency.'),
    DependencySpec('lz4', 'lz4', 'runtime', False, 'Optional LZ4 support used by selected formats.'),
    DependencySpec('lzo', 'python-lzo', 'runtime', False, 'Linux-only optional LZO support.', ('linux',)),
    DependencySpec('sv_ttk', 'sv_ttk', 'ui', False, 'Optional theme package; app should degrade gracefully.'),
    DependencySpec('PyInstaller', 'pyinstaller', 'build', False, 'Release packaging dependency.'),
    DependencySpec('pygments', 'Pygments', 'tooling', False, 'Editor/syntax highlighting dependency.'),
    DependencySpec('chlorophyll', 'chlorophyll', 'tooling', False, 'Editor highlighting theme dependency.'),
    DependencySpec('wmi', 'WMI', 'runtime', False, 'Windows-only hardware/system helper.', ('win32',)),
)


def _platform_matches(spec: DependencySpec) -> bool:
    if not spec.platforms:
        return True
    current = sys.platform
    return any(current.startswith(target) for target in spec.platforms)


def _distribution_version(distribution: str | None) -> str | None:
    if not distribution:
        return None
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def check_dependency(spec: DependencySpec) -> DependencyStatus:
    version = _distribution_version(spec.distribution)
    if not _platform_matches(spec):
        return DependencyStatus(
            import_name=spec.import_name,
            distribution=spec.distribution,
            category=spec.category,
            required=False,
            ok=True,
            version=version,
            error='skipped-on-platform',
            note=spec.note,
        )
    try:
        module = importlib.import_module(spec.import_name)
    except Exception as exc:  # pragma: no cover - exact dependency set is environment-specific
        return DependencyStatus(
            import_name=spec.import_name,
            distribution=spec.distribution,
            category=spec.category,
            required=spec.required,
            ok=False,
            version=version,
            error=f'{type(exc).__name__}: {exc}',
            note=spec.note,
        )

    module_version = getattr(module, '__version__', None)
    return DependencyStatus(
        import_name=spec.import_name,
        distribution=spec.distribution,
        category=spec.category,
        required=spec.required,
        ok=True,
        version=str(version or module_version or ''),
        error=None,
        note=spec.note,
    )


def collect_statuses(*, include_optional: bool = True, categories: Iterable[str] | None = None) -> list[DependencyStatus]:
    wanted_categories = set(categories or ())
    statuses: list[DependencyStatus] = []
    for spec in DEPENDENCIES:
        if wanted_categories and spec.category not in wanted_categories:
            continue
        if not include_optional and not spec.required:
            continue
        statuses.append(check_dependency(spec))
    return statuses


def validate_protobuf_namespace(statuses: Iterable[DependencyStatus]) -> list[str]:
    """Return namespace-specific protobuf problems beyond plain import errors."""

    problems: list[str] = []
    protobuf_status = next((status for status in statuses if status.import_name == 'google.protobuf'), None)
    if protobuf_status is None or not protobuf_status.ok:
        return problems
    try:
        google = importlib.import_module('google')
        protobuf = importlib.import_module('google.protobuf')
    except Exception as exc:  # pragma: no cover - guarded by status above
        problems.append(f'protobuf namespace re-import failed: {type(exc).__name__}: {exc}')
        return problems
    if not hasattr(google, '__path__'):
        problems.append('google namespace has no __path__; protobuf namespace may be shadowed')
    protobuf_file = getattr(protobuf, '__file__', None)
    if not protobuf_file:
        problems.append('google.protobuf has no __file__; protobuf installation may be incomplete')
    return problems


def build_report(*, include_optional: bool = True, categories: Iterable[str] | None = None) -> dict[str, object]:
    statuses = collect_statuses(include_optional=include_optional, categories=categories)
    return {
        'python': sys.version.split()[0],
        'platform': platform.platform(),
        'executable': sys.executable,
        'dependencies': [asdict(status) for status in statuses],
        'protobuf_namespace_problems': validate_protobuf_namespace(statuses),
    }


def _format_report(report: dict[str, object]) -> str:
    lines = [
        'MIO-KITCHEN runtime dependency preflight',
        f"Python: {report['python']} ({report['executable']})",
        f"Platform: {report['platform']}",
        '',
        'Dependencies:',
    ]
    for dep in report['dependencies']:
        status = 'OK' if dep['ok'] else 'MISSING'
        required = 'required' if dep['required'] else 'optional'
        version = dep['version'] or '-'
        error = f" — {dep['error']}" if dep['error'] and dep['error'] != 'skipped-on-platform' else ''
        lines.append(f"  [{status:<7}] {dep['import_name']:<18} {required:<8} {dep['category']:<8} version={version}{error}")
    problems = report.get('protobuf_namespace_problems') or []
    if problems:
        lines.append('')
        lines.append('Protobuf namespace validation:')
        lines.extend(f'  - {problem}' for problem in problems)
    return '\n'.join(lines)


def _has_blocking_failures(report: dict[str, object], *, fail_on_optional: bool = False) -> bool:
    dependencies = report['dependencies']
    for dep in dependencies:
        if dep['ok']:
            continue
        if dep['required'] or fail_on_optional:
            return True
    return bool(report.get('protobuf_namespace_problems'))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Check runtime/release dependencies before smoke tests.')
    parser.add_argument('--json', action='store_true', help='Print a machine-readable JSON report.')
    parser.add_argument(
        '--smoke-only',
        action='store_true',
        help='Check only required runtime/UI dependencies needed before GUI smoke tests.',
    )
    parser.add_argument('--required-only', action='store_true', help='Skip optional dependencies.')
    parser.add_argument('--category', action='append', choices=('runtime', 'ui', 'build', 'tooling'), help='Limit checks to one or more dependency categories.')
    parser.add_argument('--fail-on-optional', action='store_true', help='Treat optional missing dependencies as failures too.')
    parser.add_argument('--allow-missing-required', action='store_true', help='Always exit 0; useful for diagnostic CI stages.')
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    categories = args.category
    include_optional = not args.required_only
    if args.smoke_only:
        categories = ['runtime', 'ui'] if categories is None else categories
        include_optional = False
    report = build_report(include_optional=include_optional, categories=categories)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_report(report))
    if args.allow_missing_required:
        return 0
    return 1 if _has_blocking_failures(report, fail_on_optional=args.fail_on_optional) else 0


if __name__ == '__main__':  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
