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


import os
import sys
from pathlib import Path


def find_project_root(file_path: str | Path) -> Path:
    current = Path(file_path).resolve().parent
    while current != current.parent:
        if (
            (current / "src").is_dir()
            and (current / "tests").is_dir()
            and (current / "scripts").is_dir()
        ):
            return current
        current = current.parent
    raise RuntimeError(f"Project root was not found for {file_path}")


def run_test_file(file_path: str | Path, argv: list[str] | None = None) -> int:
    import pytest

    path = Path(file_path).resolve()
    root = find_project_root(path)
    previous_cwd = Path.cwd()
    try:
        os.chdir(root)
        arguments = ["-q", "--rootdir=.", "-c", "scripts/config/pytest.ini", str(path)]
        arguments.extend(sys.argv[1:] if argv is None else argv)
        return int(pytest.main(arguments))
    finally:
        os.chdir(previous_cwd)


def support_module_main(file_path: str | Path) -> int:
    path = Path(file_path).resolve()
    root = find_project_root(path)
    print(f"DIRECT_IMPORT_OK: {path.relative_to(root).as_posix()}")
    return 0


__all__ = ["find_project_root", "run_test_file", "support_module_main"]

if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
