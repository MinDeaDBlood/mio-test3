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
import ast
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_SMOKE_MARKERS = {"not-a-real", "zip-placeholder", "fake generator marker"}
PYTHON_PATH_PATTERN = re.compile(r"(?P<path>(?:tests|scripts)[/\\][\w./\\-]+\.py)")
TEST_DOUBLE_PREFIXES = ("fake", "dummy", "stub")
INTENTIONALLY_REMOVED_PATHS = {"tests/support/runtime_stubs.py"}


def _module_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _module_replacement(node: ast.AST) -> str | None:
    targets: list[ast.expr] = []
    if isinstance(node, ast.Assign):
        targets.extend(node.targets)
    elif isinstance(node, ast.AnnAssign):
        targets.append(node.target)
    for target in targets:
        if not (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Attribute)
            and isinstance(target.value.value, ast.Name)
            and target.value.value.id == "sys"
            and target.value.attr == "modules"
        ):
            continue
        module_name = _module_name(target.slice)
        if module_name:
            return module_name
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "setitem"
        and len(node.args) >= 2
    ):
        modules_arg = node.args[0]
        if (
            isinstance(modules_arg, ast.Attribute)
            and isinstance(modules_arg.value, ast.Name)
            and modules_arg.value.id == "sys"
            and modules_arg.attr == "modules"
        ):
            return _module_name(node.args[1])
    return None


def _production_module_aliases(tree: ast.AST) -> set[str]:
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name.startswith("src"):
                    aliases.add(imported.asname or imported.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("src"):
            aliases.update(imported.asname or imported.name for imported in node.names)
    return aliases


def _assigned_root_name(target: ast.expr) -> str | None:
    current = target
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _test_double_name(node: ast.AST) -> tuple[str, int] | None:
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        lowered = node.name.lower()
        if lowered.startswith(TEST_DOUBLE_PREFIXES):
            return node.name, node.lineno
    return None


def collect_violations() -> list[str]:
    violations: list[str] = []
    removed_stub = PROJECT_ROOT / "tests" / "support" / "runtime_stubs.py"
    if removed_stub.exists():
        violations.append("tests/support/runtime_stubs.py must stay removed")

    for path in sorted((PROJECT_ROOT / "scripts").rglob("*.py")):
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("tests"):
                violations.append(f"{relative}:{node.lineno} imports test code")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("tests"):
                        violations.append(f"{relative}:{node.lineno} imports test code")
            elif isinstance(node, ast.ImportFrom) and node.module == "types":
                if any(alias.name == "SimpleNamespace" for alias in node.names):
                    violations.append(
                        f"{relative}:{node.lineno} uses SimpleNamespace instead of production types"
                    )
        for match in PYTHON_PATH_PATTERN.finditer(source):
            referenced = match.group("path").replace("\\", "/")
            if referenced in INTENTIONALLY_REMOVED_PATHS:
                continue
            if not (PROJECT_ROOT / referenced).is_file():
                violations.append(f"{relative} references missing Python file {referenced}")

    for path in sorted((PROJECT_ROOT / "tests").rglob("*.py")):
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        is_runtime_scenario = "/smoke/" in f"/{relative}" or "/e2e/" in f"/{relative}"
        production_aliases = _production_module_aliases(tree) if is_runtime_scenario else set()
        for node in ast.walk(tree):
            module_name = _module_replacement(node)
            if module_name:
                violations.append(
                    f"{relative}:{getattr(node, 'lineno', 0)} replaces real module {module_name}"
                )
            if is_runtime_scenario:
                test_double = _test_double_name(node)
                if test_double:
                    name, line = test_double
                    violations.append(
                        f"{relative}:{line} defines runtime test double {name}"
                    )
                if isinstance(node, ast.ImportFrom) and node.module == "types":
                    if any(alias.name == "SimpleNamespace" for alias in node.names):
                        violations.append(
                            f"{relative}:{node.lineno} uses SimpleNamespace in a runtime scenario"
                        )
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    targets = (
                        node.targets
                        if isinstance(node, ast.Assign)
                        else [node.target]
                    )
                    for target in targets:
                        root_name = _assigned_root_name(target)
                        if root_name in production_aliases:
                            violations.append(
                                f"{relative}:{node.lineno} replaces an attribute on imported production code"
                            )
        if is_runtime_scenario:
            lowered = source.lower()
            for marker in FORBIDDEN_SMOKE_MARKERS:
                if marker in lowered:
                    violations.append(f"{relative} contains placeholder marker {marker!r}")

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject dependency stubs, module replacement, and placeholder smoke data."
    )
    parser.parse_args(argv)
    violations = collect_violations()
    if violations:
        for violation in violations:
            print(violation)
        return 1
    print("TEST_INTEGRITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
