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
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR_NAMES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
CACHE_FILE_SUFFIXES = {'.pyc', '.pyo'}


def iter_cleanup_targets(root: Path):
    for path in root.rglob('*'):
        rel_parts = path.relative_to(root).parts
        if any(part in CACHE_DIR_NAMES for part in rel_parts):
            if path.name in CACHE_DIR_NAMES:
                yield path
            continue
        if path.is_file() and path.suffix in CACHE_FILE_SUFFIXES:
            yield path


def clean(*, dry_run: bool = False) -> list[Path]:
    targets = sorted(set(iter_cleanup_targets(PROJECT_ROOT)), key=lambda item: (len(item.parts), str(item)), reverse=True)
    removed: list[Path] = []
    for target in targets:
        if not target.exists():
            continue
        removed.append(target)
        if dry_run:
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Remove generated Python cache artifacts without touching runtime log/temp folders.')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be removed without deleting it.')
    args = parser.parse_args(argv)
    removed = clean(dry_run=args.dry_run)
    action = 'Would remove' if args.dry_run else 'Removed'
    for path in removed:
        print(f'{action}: {path.relative_to(PROJECT_ROOT)}')
    print('WORKSPACE_ARTIFACT_CLEAN_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
