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
import json
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class SystemDependencyIssue:
    name: str
    detail: str
    remediation: str


@dataclass(frozen=True)
class SystemDependencyReport:
    platform: str
    issues: list[SystemDependencyIssue]

    @property
    def ok(self) -> bool:
        return not self.issues


LZO_HEADER_CANDIDATES = (
    Path('/usr/include/lzo/lzo1.h'),
    Path('/usr/local/include/lzo/lzo1.h'),
    Path('/opt/homebrew/include/lzo/lzo1.h'),
)


def _pkg_config_has(package: str) -> bool:
    if not shutil.which('pkg-config'):
        return False
    result = subprocess.run(['pkg-config', '--exists', package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def build_report() -> SystemDependencyReport:
    system = platform.system().lower()
    issues: list[SystemDependencyIssue] = []
    if system == 'linux':
        has_lzo_header = any(path.exists() for path in LZO_HEADER_CANDIDATES) or _pkg_config_has('lzo2')
        if not has_lzo_header:
            issues.append(
                SystemDependencyIssue(
                    name='lzo2-development-headers',
                    detail='python-lzo requires the C header lzo/lzo1.h on Linux.',
                    remediation='Install liblzo2-dev on Debian/Ubuntu, lzo-devel on Fedora/RHEL, or the equivalent package for your distribution.',
                )
            )
    return SystemDependencyReport(platform=platform.platform(), issues=issues)


def _format_report(report: SystemDependencyReport) -> str:
    lines = ['MIO-KITCHEN known system prerequisite preflight', f'Platform: {report.platform}']
    if report.issues:
        lines.append('Issues:')
        for issue in report.issues:
            lines.append(f'  - [{issue.name}] {issue.detail}')
            lines.append(f'    Fix: {issue.remediation}')
    else:
        lines.append('SYSTEM_DEPENDENCIES_OK')
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate known OS-level release/build prerequisites before pip install/build checks. This is an extensible preflight, not a complete system verifier.')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--allow-missing', action='store_true', help='Report missing system dependencies without failing.')
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        payload = asdict(report)
        payload['ok'] = report.ok
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_format_report(report))
    if args.allow_missing:
        return 0
    return 0 if report.ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
