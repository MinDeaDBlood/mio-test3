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
import json
import re
from collections import defaultdict
from pathlib import Path

from tests.support.paths import PROJECT_ROOT
APP_ROOT = PROJECT_ROOT / "src" / "app"
LANGUAGE_ROOT = PROJECT_ROOT / "languages"
_RESOLVER_METHODS = {
    "resolve",
    "resolve_optional",
    "resolve_ui_text",
    "resolve_required_ui_text",
}
_CATALOG_API = _RESOLVER_METHODS | {
    "REFERENCE_LANGUAGE",
    "clear_reference",
    "current_language",
    "current_language_file",
    "has",
    "load_map",
    "load_reference_map",
    "set_reference_source",
    "set_source",
}
_OLD_GENERIC_KEYS = {
    "attribute",
    "cancel",
    "ok",
    "pack",
    "path",
    "refresh",
    "run",
    "set_all",
    "warning_title",
}


def _module_path(module_name: str) -> Path | None:
    candidate = PROJECT_ROOT.joinpath(*module_name.split(".")).with_suffix(".py")
    return candidate if candidate.exists() else None


def _string_constants(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    constants: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            constants[node.targets[0].id] = node.value.value
    return constants


def _imported_key_modules(tree: ast.Module) -> dict[str, dict[str, str]]:
    modules: dict[str, dict[str, str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            for imported in node.names:
                candidates: tuple[str, ...] = ()
                if imported.name == "keys":
                    candidates = (f"{module_name}.keys",)
                elif imported.name.endswith("_keys"):
                    candidates = (f"{module_name}.{imported.name}",)
                for candidate in candidates:
                    module_path = _module_path(candidate)
                    if module_path is not None:
                        modules[imported.asname or imported.name] = _string_constants(
                            module_path
                        )
        elif isinstance(node, ast.Import):
            for imported in node.names:
                if not (
                    imported.name.endswith(".keys") or imported.name.endswith("_keys")
                ):
                    continue
                module_path = _module_path(imported.name)
                if module_path is not None:
                    modules[imported.asname or imported.name.rsplit(".", 1)[-1]] = (
                        _string_constants(module_path)
                    )
    return modules


def _is_self_catalog_attribute(node: ast.Attribute) -> bool:
    value = node.value
    return (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id == "self"
        and value.attr in {"_language", "_texts", "language", "texts"}
    )


def _app_localization_usage() -> tuple[dict[str, set[str]], list[str]]:
    owners: defaultdict[str, set[str]] = defaultdict(set)
    violations: list[str] = []
    for source_path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), filename=str(source_path)
        )
        relative_path = str(source_path.relative_to(PROJECT_ROOT))
        key_modules = _imported_key_modules(tree)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and (
                (isinstance(node.value, ast.Name) and node.value.id == "lang")
                or _is_self_catalog_attribute(node)
            ):
                if node.attr in _CATALOG_API:
                    continue
                parent = parents.get(node)
                if isinstance(parent, ast.Call) and parent.func is node:
                    continue
                violations.append(
                    f"{relative_path}:{node.lineno} accesses localization key "
                    f"{node.attr!r} directly instead of an owned key constant"
                )
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _RESOLVER_METHODS
                and node.args
            ):
                continue
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                violations.append(
                    f"{relative_path}:{node.lineno} resolves raw key literal "
                    f"{first_arg.value!r}"
                )
                continue
            if (
                isinstance(first_arg, ast.Attribute)
                and isinstance(first_arg.value, ast.Name)
                and first_arg.value.id in key_modules
            ):
                key_value = key_modules[first_arg.value.id].get(first_arg.attr)
                if key_value:
                    owners[key_value].add(relative_path)
                    if (
                        re.fullmatch(r"(?:warn|text|t)\d+", key_value)
                        or key_value in _OLD_GENERIC_KEYS
                    ):
                        violations.append(
                            f"{relative_path}:{node.lineno} uses legacy/shared key "
                            f"{key_value!r}"
                        )
    return dict(owners), violations


def test_app_localization_keys_are_explicit_and_file_owned() -> None:
    owners, violations = _app_localization_usage()
    reused = {key: sorted(paths) for key, paths in owners.items() if len(paths) > 1}
    assert violations == []
    assert reused == {}, f"App localization keys have multiple owners: {reused}"


def test_every_owned_app_key_exists_in_every_bundled_language() -> None:
    owners, _violations = _app_localization_usage()
    assert owners, "No app localization keys were discovered"
    for language_file in sorted(LANGUAGE_ROOT.glob("*.json")):
        translations = json.loads(language_file.read_text(encoding="utf-8"))
        missing = [
            key
            for key in owners
            if not isinstance(translations.get(key), str)
            or not translations[key].strip()
            or translations[key].strip().lower() == "none"
        ]
        assert missing == [], f"{language_file.name} is missing app keys: {missing}"

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
