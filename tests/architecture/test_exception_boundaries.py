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

LOGIC_ROOT = PROJECT_ROOT / "src" / "logic"
ALLOWED_BROAD_EXCEPTION_BOUNDARIES = {
    ("plugins/module_manager.py", "load_plugins_and_notify"),
    ("plugins/module_manager.py", "register_plugin"),
    ("projects/unpack/gpt/service.py", "extract_gpt_partitions"),
}


def _broad_exception_handlers(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    handlers: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not isinstance(node.type, ast.Name) or node.type.id != "Exception":
            continue
        current: ast.AST | None = node
        function_name = "<module>"
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_name = current.name
                break
        handlers.append((function_name, node.lineno))
    return handlers


def test_logic_broad_exceptions_are_limited_to_explicit_isolation_boundaries() -> None:
    violations: list[str] = []
    for path in sorted(LOGIC_ROOT.rglob("*.py")):
        relative = path.relative_to(LOGIC_ROOT).as_posix()
        for function_name, line in _broad_exception_handlers(path):
            if (relative, function_name) not in ALLOWED_BROAD_EXCEPTION_BOUNDARIES:
                violations.append(f"{relative}:{line} in {function_name}")
    assert violations == []


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
