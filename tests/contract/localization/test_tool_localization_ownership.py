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
TOOLS_ROOT = PROJECT_ROOT / "src" / "ui" / "tabs" / "tools"
LANGUAGE_ROOT = PROJECT_ROOT / "languages"

_PREFIX_BY_MODULE = {
    "keys.py": ("tools_view_", "tools_toolbox_"),
    "allow_selinux_audit/keys.py": ("tools_allow_selinux_audit_",),
    "byte_calculator/keys.py": ("tools_byte_calculator_",),
    "decrypt_xtc_xml/keys.py": ("tools_decrypt_xtc_xml_",),
    "disable_avb_in_fstab/keys.py": ("tools_disable_avb_",),
    "disable_encryption/keys.py": ("tools_disable_encryption_",),
    "download_firmware/keys.py": ("tools_download_firmware_",),
    "get_file_info/keys.py": ("tools_get_file_info_",),
    "magisk_patch/keys.py": ("tools_magisk_patch_",),
    "merge_qualcomm_image/keys.py": ("tools_merge_qualcomm_image_",),
    "merge_super/keys.py": ("tools_merge_super_",),
    "mtk_port_tool/keys.py": ("tools_mtk_port_",),
    "split_super/keys.py": ("tools_split_super_",),
    "trim_raw_image/keys.py": ("tools_trim_raw_image_",),
}

_ALLOWED_LANGUAGE_METHODS = {
    "current_language",
    "current_language_file",
    "resolve",
    "resolve_required_ui_text",
    "resolve_ui_text",
}


def _key_constants(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id.isupper()
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            result[target.id] = node.value.value
    return result


def _all_tool_keys() -> dict[str, tuple[Path, str]]:
    result: dict[str, tuple[Path, str]] = {}
    duplicates: defaultdict[str, list[str]] = defaultdict(list)
    for relative, prefixes in _PREFIX_BY_MODULE.items():
        path = TOOLS_ROOT / relative
        for constant, key in _key_constants(path).items():
            duplicates[key].append(f"{relative}:{constant}")
            assert key.startswith(prefixes), (
                f"{relative}:{constant} owns {key!r}, but tool keys must start with {prefixes}"
            )
            result[key] = (path, constant)
    repeated = {key: owners for key, owners in duplicates.items() if len(owners) > 1}
    assert repeated == {}, f"Tool localization keys are reused: {repeated}"
    return result


def _language_attribute(node: ast.Attribute) -> bool:
    value = node.value
    if isinstance(value, ast.Name) and value.id in {"language", "texts"}:
        return True
    return (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id == "self"
        and value.attr in {"_language", "_texts"}
    )


def _literal_text(expression: ast.AST) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.JoinedStr):
        return "".join(
            value.value
            for value in expression.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        return _literal_text(expression.left) or _literal_text(expression.right)
    return None


def test_every_tool_control_key_has_one_owner() -> None:
    keys = _all_tool_keys()
    assert len(keys) >= 230


def test_every_tool_key_exists_in_every_bundled_language() -> None:
    tool_keys = _all_tool_keys()
    for language_file in sorted(LANGUAGE_ROOT.glob("*.json")):
        translations = json.loads(language_file.read_text(encoding="utf-8"))
        missing = [
            key
            for key in tool_keys
            if not isinstance(translations.get(key), str)
            or not translations[key].strip()
            or translations[key].strip().lower() == "none"
        ]
        assert missing == [], f"{language_file.name} is missing tool keys: {missing}"


def test_tool_views_use_key_modules_instead_of_dynamic_shared_attributes() -> None:
    violations: list[str] = []
    for source_path in sorted(TOOLS_ROOT.rglob("*.py")):
        if source_path.name == "keys.py":
            continue
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), filename=str(source_path)
        )
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and _language_attribute(node)
                and node.attr not in _ALLOWED_LANGUAGE_METHODS
            ):
                violations.append(
                    f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} uses {ast.unparse(node)}"
                )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr
                in {"resolve", "resolve_required_ui_text", "resolve_ui_text"}
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                violations.append(
                    f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} resolves a raw key literal "
                    f"{node.args[0].value!r}"
                )
    assert violations == []


def test_tool_views_have_no_hardcoded_translatable_widget_or_dialog_text() -> None:
    violations: list[str] = []
    visible_keywords = {"text", "title", "message", "label", "ok", "cancel"}
    visible_positional_calls = {"ask_win", "info_win", "message_pop", "warn_win"}
    for source_path in sorted(TOOLS_ROOT.rglob("*.py")):
        if source_path.name == "keys.py":
            continue
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
            for location, expression in candidates:
                literal = _literal_text(expression)
                if literal and re.search(r"[A-Za-zА-Яа-яЁё]", literal):
                    violations.append(
                        f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                        f"hardcodes visible {location}: {literal!r}"
                    )
    assert violations == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
