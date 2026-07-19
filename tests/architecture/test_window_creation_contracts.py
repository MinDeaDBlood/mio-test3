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

import ast
from pathlib import Path

PROJECT_ROOT = _DIRECT_PROJECT_ROOT
UI_ROOT = PROJECT_ROOT / "src" / "ui"


def _ui_sources() -> list[Path]:
    return sorted(path for path in UI_ROOT.rglob("*.py") if path.is_file())


def test_ui_does_not_create_raw_tk_toplevel_windows() -> None:
    violations: list[str] = []
    for path in _ui_sources():
        if path == UI_ROOT / "common" / "windowing.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "tkinter":
                if any(alias.name == "Toplevel" for alias in node.names):
                    violations.append(path.relative_to(PROJECT_ROOT).as_posix())
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id in {"tk", "tkinter"}
                    and node.func.attr == "Toplevel"
                ):
                    violations.append(path.relative_to(PROJECT_ROOT).as_posix())
    assert violations == []


def test_partition_pack_always_opens_options_window() -> None:
    composition = (
        PROJECT_ROOT / "src/app/composition/partition_pack.py"
    ).read_text(encoding="utf-8")
    window = (
        PROJECT_ROOT / "src/ui/tabs/project/pack/partition/window.py"
    ).read_text(encoding="utf-8")

    assert "auto_start" not in composition
    assert "auto_start" not in window
    assert "self.withdraw()" not in window


def test_zip_pack_prompt_is_a_real_owned_window() -> None:
    source = (
        PROJECT_ROOT / "src/ui/tabs/project/pack/zip_prompt.py"
    ).read_text(encoding="utf-8")

    assert "Toplevel(master=host_window)" in source
    assert "dialog.grab_set()" in source
    assert "dialog.wait_window()" in source


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
