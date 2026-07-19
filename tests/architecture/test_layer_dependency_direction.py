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

from tests.support.paths import PROJECT_ROOT
SRC_ROOT = PROJECT_ROOT / "src"

_ALLOWED_PROJECT_LAYERS = {
    "core": {"core"},
    "logic": {"core", "logic"},
    "platform": {"core", "platform"},
    "ui": {"ui"},
    "app": {"app", "core", "logic", "platform", "pro", "ui"},
}


def _project_imports(path: Path) -> tuple[tuple[int, str], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.lineno, node.module))
    return tuple((line, module) for line, module in imports if module.startswith("src."))


def test_project_layers_follow_one_direction() -> None:
    violations: list[str] = []
    for layer, allowed in _ALLOWED_PROJECT_LAYERS.items():
        for path in sorted((SRC_ROOT / layer).rglob("*.py")):
            for line, imported in _project_imports(path):
                imported_layer = imported.split(".", 2)[1]
                if imported_layer not in allowed:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{line} imports {imported}"
                    )
    assert violations == []


def test_removed_config_and_infrastructure_packages_do_not_return() -> None:
    assert not (SRC_ROOT / "config").exists()
    assert not (SRC_ROOT / "infrastructure").exists()


def test_owned_modules_stay_below_four_hundred_lines() -> None:
    oversized: list[str] = []
    for layer in ("ui", "app", "logic", "platform"):
        for path in sorted((SRC_ROOT / layer).rglob("*.py")):
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > 400:
                oversized.append(
                    f"{path.relative_to(PROJECT_ROOT).as_posix()}:{line_count}"
                )
    assert oversized == []

_FORBIDDEN_APP_MODULES = {
    "configparser",
    "json",
    "requests",
    "shutil",
    "subprocess",
    "urllib",
    "webbrowser",
}
_FORBIDDEN_APP_CALLS = {
    "mkdir",
    "touch",
    "read_bytes",
    "read_text",
    "write_bytes",
    "write_text",
    "unlink",
    "rmdir",
}
_FORBIDDEN_OS_PATH_CALLS = {"exists", "isdir", "isfile", "getsize"}
_FORBIDDEN_APP_NAME_CALLS = _FORBIDDEN_APP_CALLS | {"open"}


def test_application_layer_does_not_execute_platform_io_directly() -> None:
    violations: list[str] = []
    for path in sorted((SRC_ROOT / "app").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in _FORBIDDEN_APP_MODULES:
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} imports {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".", 1)[0] in _FORBIDDEN_APP_MODULES:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} imports {node.module}"
                    )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_APP_NAME_CALLS:
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} calls {node.func.id}"
                    )
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in _FORBIDDEN_APP_CALLS:
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} calls {node.func.attr}"
                        )
                    if (
                        node.func.attr in _FORBIDDEN_OS_PATH_CALLS
                        and isinstance(node.func.value, ast.Attribute)
                        and isinstance(node.func.value.value, ast.Name)
                        and node.func.value.value.id == "os"
                        and node.func.value.attr == "path"
                    ):
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} calls os.path.{node.func.attr}"
                        )
    assert violations == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
