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

import ast

PROJECT_ROOT = _DIRECT_PROJECT_ROOT
UI_ROOT = PROJECT_ROOT / "src" / "ui"
SMOKE_FILES = (
    PROJECT_ROOT / "tests" / "smoke" / "windows.py",
    PROJECT_ROOT / "tests" / "smoke" / "window_catalog.py",
)


def _direct_toplevel_subclasses() -> set[str]:
    result: set[str] = set()
    for path in UI_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = {base.id for base in node.bases if isinstance(base, ast.Name)}
            if "Toplevel" in base_names:
                result.add(node.name)
    return result


def _declared_smoke_coverage() -> set[str]:
    result: set[str] = set()
    for path in SMOKE_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(
                isinstance(target, ast.Name) and target.id == "COVERED_TOPLEVEL_CLASSES"
                for target in node.targets
            ):
                continue
            values = ast.literal_eval(node.value)
            result.update(str(value) for value in values)
    return result


def test_every_direct_toplevel_class_is_exercised_by_window_smoke() -> None:
    assert _declared_smoke_coverage() == _direct_toplevel_subclasses()


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
