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
import re

from tests.support.paths import PROJECT_ROOT
UI_ROOT = PROJECT_ROOT / "src" / "ui"
APP_ROOT = PROJECT_ROOT / "src" / "app"


def _literal_text(expression: ast.AST) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.JoinedStr):
        return "".join(
            item.value
            for item in expression.values
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        return _literal_text(expression.left) or _literal_text(expression.right)
    return None


def test_visible_ui_text_is_not_embedded_as_translatable_literals() -> None:
    violations: list[str] = []
    visible_keywords = {
        "text",
        "title",
        "message",
        "label",
        "ok",
        "cancel",
        "help",
        "description",
        "prompt",
        "heading",
    }
    visible_positional_calls = {
        "_console_print",
        "ask_win",
        "info_win",
        "message_pop",
        "warn_win",
    }
    for root in (UI_ROOT, APP_ROOT):
        for source_path in sorted(root.rglob("*.py")):
            tree = ast.parse(
                source_path.read_text(encoding="utf-8"), filename=str(source_path)
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                call_name = (
                    node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else node.func.id
                    if isinstance(node.func, ast.Name)
                    else ""
                )
                candidates: list[tuple[str, ast.AST]] = []
                if call_name == "title" and node.args:
                    candidates.append(("title", node.args[0]))
                if call_name in visible_positional_calls and node.args:
                    candidates.append(("first argument", node.args[0]))
                candidates.extend(
                    (keyword.arg or "", keyword.value)
                    for keyword in node.keywords
                    if keyword.arg in visible_keywords
                )

                if call_name in {
                    "resolve",
                    "resolve_optional",
                    "resolve_ui_text",
                    "resolve_required_ui_text",
                }:
                    candidates.extend(
                        ("localization default", keyword.value)
                        for keyword in node.keywords
                        if keyword.arg == "default"
                    )
                if call_name == "getattr" and len(node.args) >= 3:
                    owner = node.args[0]
                    if (
                        isinstance(owner, ast.Name)
                        and owner.id in {"texts", "language", "lang"}
                    ) or (
                        isinstance(owner, ast.Attribute)
                        and owner.attr in {"texts", "_texts", "language", "_language"}
                    ):
                        candidates.append(("localization fallback", node.args[2]))
                for location, expression in candidates:
                    literal = _literal_text(expression)
                    if literal and re.search(r"[A-Za-zА-Яа-яЁё]", literal):
                        # input_.text is a functional default value, such as a file name or
                        # device codename. It is not a user-interface label or message.
                        if call_name == "input_" and location == "text":
                            continue
                        violations.append(
                            f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                            f"hardcodes visible {location}: {literal!r}"
                        )
    assert violations == []


def test_localization_objects_do_not_hide_missing_keys_with_getattr_defaults() -> None:
    violations: list[str] = []
    catalog_names = {"lang", "texts", "language"}
    catalog_attributes = {"lang", "texts", "_texts", "language", "_language"}
    for root in (UI_ROOT, APP_ROOT):
        for source_path in sorted(root.rglob("*.py")):
            tree = ast.parse(
                source_path.read_text(encoding="utf-8"), filename=str(source_path)
            )
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "getattr"
                    and len(node.args) >= 3
                ):
                    owner = node.args[0]
                    is_catalog = (
                        isinstance(owner, ast.Name) and owner.id in catalog_names
                    ) or (
                        isinstance(owner, ast.Attribute)
                        and owner.attr in catalog_attributes
                    )
                    if is_catalog:
                        violations.append(
                            f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                            "uses a fallback for a localization key"
                        )
    assert violations == []


def test_localization_requires_explicit_key_resolution() -> None:
    runtime_source = (APP_ROOT / "localization_runtime.py").read_text(encoding="utf-8")
    protocol_source = (UI_ROOT / "localization.py").read_text(encoding="utf-8")
    assert "def __getattr__" not in runtime_source
    assert "def __getattr__" not in protocol_source


def test_localization_catalog_is_not_used_as_a_dynamic_attribute_bag() -> None:
    allowed_attributes = {
        "REFERENCE_LANGUAGE",
        "clear_reference",
        "current_language",
        "current_language_file",
        "has",
        "is_loaded",
        "load_map",
        "load_reference_map",
        "reference_language",
        "reference_language_file",
        "resolve",
        "resolve_optional",
        "resolve_required_ui_text",
        "resolve_ui_text",
        "set_reference_source",
        "set_source",
    }
    violations: list[str] = []
    catalog_names = {"lang", "texts", "language"}
    catalog_attributes = {"lang", "texts", "_texts", "language", "_language"}

    for root in (UI_ROOT, APP_ROOT):
        for source_path in sorted(root.rglob("*.py")):
            tree = ast.parse(
                source_path.read_text(encoding="utf-8"), filename=str(source_path)
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.Attribute):
                    continue
                owner = node.value
                is_catalog = (
                    isinstance(owner, ast.Name) and owner.id in catalog_names
                ) or (
                    isinstance(owner, ast.Attribute)
                    and owner.attr in catalog_attributes
                )
                if is_catalog and node.attr not in allowed_attributes:
                    violations.append(
                        f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                        f"uses dynamic localization attribute {node.attr!r}"
                    )
    assert violations == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
