#!/usr/bin/env python3
"""Run strict static checks for the Plugin Store and Tk integration boundaries."""

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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "scripts/config/mypy-typed-boundaries.ini"
TARGETS = (
    "src/core/contracts.py",
    "src/logic/plugins/store_models.py",
    "src/logic/plugins/runtime/registry.py",
    "src/logic/plugins/catalog/service.py",
    "src/logic/plugins/config/service.py",
    "src/logic/plugins/metadata/service.py",
    "src/logic/plugins/uninstall/service.py",
    "src/logic/plugins/store_service.py",
    "src/logic/plugins/store_install/service.py",
    "src/logic/plugins/uninstall/result.py",
    "src/app/runtime/contexts/contracts.py",
    "src/app/runtime/flags.py",
    "src/app/ui_scheduler.py",
    "src/app/ui_feedback.py",
    "src/app/ui_tasks.py",
    "src/app/plugins/runtime.py",
    "src/app/plugins/store",
    "src/app/composition/plugin_store.py",
    "src/ui/common/titlebar.py",
    "src/ui/common/window_appearance.py",
    "src/ui/common/windowing.py",
    "src/app/settings/tab_controller.py",
    "src/app/settings/presentation_controller.py",
    "src/app/settings/actions.py",
    "src/ui/common/geometry.py",
    "src/ui/common/loading_animation.py",
    "src/ui/window_sections/main_window_layout.py",
    "src/ui/tabs/plugins/store",
    "src/ui/welcome",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run mypy checks for typed architecture boundaries.')
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    parser.parse_args(arguments)
    try:
        from mypy import api as mypy_api
    except ImportError:
        print(
            "mypy is required. Install requirements-quality.txt before running this check.",
            file=sys.stderr,
        )
        return 2

    stdout, stderr, status = mypy_api.run(["--config-file", str(CONFIG_PATH), *TARGETS])
    if stdout:
        print(stdout, end="")
    if stderr:
        print(stderr, end="", file=sys.stderr)
    if status == 0:
        print("TYPED_BOUNDARIES_OK")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
