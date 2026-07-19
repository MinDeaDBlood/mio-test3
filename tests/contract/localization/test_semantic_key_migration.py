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


import json
import re

from src.app.localization_runtime import LangUtils

from tests.support.paths import PROJECT_ROOT

LANGUAGE_DIR = PROJECT_ROOT / "languages"
OPAQUE_KEY = re.compile(r"(?:text|t)\d+\Z")


def _valid_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().lower() != "none"
    )


def test_bundled_languages_contain_no_opaque_migration_keys() -> None:
    violations: dict[str, list[str]] = {}
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        translations = json.loads(language_file.read_text(encoding="utf-8"))
        opaque = sorted(key for key in translations if OPAQUE_KEY.fullmatch(key))
        if opaque:
            violations[language_file.name] = opaque
    assert violations == {}


def test_runtime_resolves_only_the_requested_semantic_key() -> None:
    resolver = LangUtils()
    resolver.load_map({"text105": "legacy", "main_window_close": "Close"})

    assert resolver.resolve_ui_text("main_window_close") == "Close"
    assert resolver.resolve("clean", default="missing") == "missing"


def test_localization_alias_module_is_removed() -> None:
    assert not (PROJECT_ROOT / "src/app/localization_aliases.py").exists()
    runtime_source = (PROJECT_ROOT / "src/app/localization_runtime.py").read_text(
        encoding="utf-8"
    )
    assert "LOCALIZATION_ALIASES" not in runtime_source
    assert "compatibility aliases" not in runtime_source


def test_corrected_file_picker_keys_exist_independently() -> None:
    corrected_keys = {
        "allow_selinux_audit_select_log_file_title",
        "trim_raw_image_select_input_file_title",
    }
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        translations = json.loads(language_file.read_text(encoding="utf-8"))
        for semantic_key in corrected_keys:
            assert _valid_text(translations.get(semantic_key)), (
                f"{language_file.name}: missing file picker title {semantic_key}"
            )


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
