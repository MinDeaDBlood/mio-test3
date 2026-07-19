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

from tests.support.paths import PROJECT_ROOT
LANGUAGE_DIR = PROJECT_ROOT / "languages"
UI_ROOT = PROJECT_ROOT / "src" / "ui"

CONTROL_TEXTS = {
    "main_window_title": "MIO-KITCHEN",
    "debugger_info_brand_label": "MIO-KITCHEN",
    "about_brand_heading": "MIO-KITCHEN",
    "home_brand_name": "MIO-KITCHEN",
    "plugins_module_dialogs_default_author_value": "MIO-KITCHEN",
    "update_window_brand_label": "MIO-KITCHEN",
    "window_sections_right_panel_brand_title": "MIO-KITCHEN",
    "tools_magisk_patch_window_is_64bit_option_label": "IS64BIT",
    "tools_magisk_patch_window_keep_verity_option_label": "KEEPVERITY",
    "tools_magisk_patch_window_keep_force_encrypt_option_label": "KEEPFORCEENCRYPT",
    "tools_magisk_patch_window_recovery_mode_option_label": "RECOVERYMODE",
}


def test_each_requested_control_has_its_own_localization_key_in_every_language() -> (
    None
):
    assert len(CONTROL_TEXTS) == len(set(CONTROL_TEXTS))
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        translations = json.loads(language_file.read_text(encoding="utf-8"))
        for key, expected_value in CONTROL_TEXTS.items():
            assert translations.get(key) == expected_value, (
                f"{language_file.name}: {key} must exist as an independent control key"
            )


def test_requested_visible_literals_are_not_hardcoded_in_ui() -> None:
    forbidden = set(CONTROL_TEXTS.values())
    violations: list[str] = []
    for source_path in sorted(UI_ROOT.rglob("*.py")):
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), filename=str(source_path)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value in forbidden:
                violations.append(
                    f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} hardcodes {node.value!r}"
                )
    assert violations == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
