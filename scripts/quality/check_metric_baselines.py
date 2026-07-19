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
from pathlib import Path


from src.app.metrics_baseline import METRIC_BASELINES

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED = {
    'startup.total',
    'project_workspace_open',
    'plugin_manager_open',
    'plugin_store_open',
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate configured runtime metric baselines.')
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    parser.parse_args(arguments)
    missing = sorted(REQUIRED.difference(METRIC_BASELINES))
    if missing:
        raise SystemExit('Missing metric baselines: ' + ', '.join(missing))
    print('METRIC_BASELINES_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
