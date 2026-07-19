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
    _direct_relative = (
        _DirectPath(__file__)
        .resolve()
        .relative_to(_DIRECT_PROJECT_ROOT)
        .with_suffix("")
    )
    __package__ = ".".join(_direct_relative.parts[:-1])

import ast
import importlib
import json

import pytest

from src.ui.assets import images
from src.ui.assets.loading_indicator import get_loading_indicator
from src.app.settings.theme import SUPPORTED_THEMES as APP_SUPPORTED_THEMES
from src.ui.common.themes.identifiers import (
    SUPPORTED_THEMES as UI_SUPPORTED_THEMES,
)
from src.logic.tools.mtk_port_tool.profiles import default_support_chipset_profiles
from src.ui.common.byte_size import format_localized_byte_size
from src.ui.common.technical_choices import (
    TECHNICAL_VALUE_KEYS,
    build_choice_set,
)
from src.ui.tabs.tools.mtk_port_tool import keys as mtk_keys
from src.ui.tabs.tools.mtk_port_tool.labels import FLAG_LABEL_KEYS, PROFILE_LABEL_KEYS
from tests.support.paths import PROJECT_ROOT

LANGUAGE_DIR = PROJECT_ROOT / "languages"
UI_ROOT = PROJECT_ROOT / "src" / "ui"

MTK_REQUIRED_KEYS = (
    set(PROFILE_LABEL_KEYS.values())
    | set(FLAG_LABEL_KEYS.values())
    | {
        mtk_keys.PROFILE_CUSTOM,
        mtk_keys.FLAG_CUSTOM,
    }
)


class _Catalog:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def resolve_required_ui_text(self, key: str) -> str:
        return self.values[key]


def test_every_technical_choice_key_exists_in_every_language() -> None:
    required_keys = set(TECHNICAL_VALUE_KEYS.values())
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        values = json.loads(language_file.read_text(encoding="utf-8"))
        missing = sorted(
            key
            for key in required_keys
            if not isinstance(values.get(key), str) or not values[key].strip()
        )
        assert missing == [], (
            f"{language_file.name} is missing technical labels: {missing}"
        )


def test_every_mtk_profile_and_action_key_exists_in_every_language() -> None:
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        values = json.loads(language_file.read_text(encoding="utf-8"))
        missing = sorted(
            key
            for key in MTK_REQUIRED_KEYS
            if not isinstance(values.get(key), str) or not values[key].strip()
        )
        assert missing == [], f"{language_file.name} is missing MTK labels: {missing}"


def test_bundled_mtk_profiles_and_flags_have_localization_keys() -> None:
    profiles = default_support_chipset_profiles()
    assert set(profiles).issubset(PROFILE_LABEL_KEYS)
    bundled_flags = {
        flag_name
        for profile in profiles.values()
        for flag_name in profile.get("flags", {})
    }
    assert bundled_flags.issubset(FLAG_LABEL_KEYS)


def test_all_bundled_technical_choice_sets_have_unique_labels() -> None:
    choice_sets = (
        ("raw", "sparse", "dat", "br"),
        (
            "new.dat.br",
            "new.dat",
            "new.dat.xz",
            "img",
            "sparse",
            "payload",
            "super",
            "update.app",
            "zst",
        ),
        ("ext", "f2fs", "erofs"),
        ("boot", "recovery", "vendor_boot"),
        ("make_ext4fs", "mke2fs+e2fsdroid"),
        ("lz4", "lz4hc", "lzma", "deflate", "zstd"),
        ("qti_dynamic_partitions", "main", "mot_dp_group"),
        ("arm64-v8a", "armeabi-v7a", "x86", "x86_64"),
        ("utf-8", "gbk", "gb2312", "utf-16"),
        ("B", "KB", "MB", "GB", "TB", "PB", "EB"),
        ("KiB", "MiB", "GiB", "TiB"),
        ("light", "dark"),
    )
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        values = json.loads(language_file.read_text(encoding="utf-8"))
        catalog = _Catalog(values)
        for choice_values in choice_sets:
            choices = build_choice_set(catalog, choice_values)
            assert len(choices.labels) == len(set(choices.labels))


def test_byte_sizes_are_formatted_with_localized_unit_keys() -> None:
    catalog = _Catalog(
        {
            TECHNICAL_VALUE_KEYS["B"]: "bytes",
            TECHNICAL_VALUE_KEYS["KB"]: "kilobytes",
            TECHNICAL_VALUE_KEYS["MB"]: "megabytes",
            TECHNICAL_VALUE_KEYS["GB"]: "gigabytes",
            TECHNICAL_VALUE_KEYS["TB"]: "terabytes",
            TECHNICAL_VALUE_KEYS["PB"]: "petabytes",
            TECHNICAL_VALUE_KEYS["EB"]: "exabytes",
        }
    )
    assert format_localized_byte_size(0, texts=catalog) == "0.00 bytes"
    assert format_localized_byte_size(1024, texts=catalog) == "1.00 kilobytes"
    assert format_localized_byte_size(1024**2, texts=catalog) == "1.00 megabytes"


def test_super_group_labels_are_short_and_keep_internal_values() -> None:
    expected_labels = {
        "qti_dynamic_partitions": "Qualcomm",
        "main": "MTK",
        "mot_dp_group": "Moto",
    }
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        values = json.loads(language_file.read_text(encoding="utf-8"))
        choices = build_choice_set(
            _Catalog(values),
            tuple(expected_labels),
        )
        for technical_value, expected_label in expected_labels.items():
            assert choices.label_for(technical_value) == expected_label
            selected_index = choices.index_for(technical_value)
            assert choices.value_at(selected_index) == technical_value


def test_format_labels_use_exact_technical_names_in_every_language() -> None:
    expected_labels = {
        "raw": "raw",
        "sparse": "sparse",
        "dat": "new.dat",
        "br": "new.dat.br",
        "new.dat": "new.dat",
        "new.dat.br": "new.dat.br",
        "new.dat.xz": "new.dat.xz",
        "img": "img",
        "payload": "payload",
        "super": "super",
        "update.app": "update.app",
        "zst": "zst",
    }
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        values = json.loads(language_file.read_text(encoding="utf-8"))
        for technical_value, expected_label in expected_labels.items():
            localization_key = TECHNICAL_VALUE_KEYS[technical_value]
            assert values[localization_key] == expected_label


def test_pack_partition_ui_offers_only_supported_output_choices() -> None:
    from src.ui.tabs.project.pack.registry import get_output_values

    assert get_output_values() == ("raw", "sparse", "dat", "br")


def test_localized_labels_are_not_used_to_restore_technical_values() -> None:
    source = (UI_ROOT / "common" / "technical_choices.py").read_text(encoding="utf-8")
    assert "def value_for" not in source



def test_app_and_ui_theme_identifiers_match() -> None:
    assert APP_SUPPORTED_THEMES == UI_SUPPORTED_THEMES == {"dark", "light"}

def test_loading_indicator_accepts_only_technical_theme_identifiers() -> None:
    assert (
        get_loading_indicator("dark") is images.loading_indicator_dark
    )
    assert (
        get_loading_indicator("light") is images.loading_indicator_light
    )
    assert not hasattr(images, "loading_dark_byte")
    assert not hasattr(images, "loading_light_byte")
    assert not hasattr(images, "dark_theme_loading_image_bytes")
    assert not hasattr(images, "light_theme_loading_image_bytes")
    assert not hasattr(images, "icon_byte")
    assert not hasattr(images, "none_byte")
    assert not hasattr(images, "error_logo_byte")
    with pytest.raises(ValueError):
        get_loading_indicator("Dark")


def test_technical_names_requested_by_user_are_language_catalog_entries() -> None:
    expected_values = {"Magisk", "vbmeta", "fs_config", "file_contexts"}
    assert expected_values.issubset(TECHNICAL_VALUE_KEYS)




def test_theme_and_image_resource_names_are_unambiguous() -> None:
    image_source = (UI_ROOT / "assets" / "images.py").read_text(encoding="utf-8")
    assert "app_icon: bytes" in image_source
    assert "placeholder_image: bytes" in image_source
    assert "loading_indicator_dark: bytes" in image_source
    assert "loading_indicator_light: bytes" in image_source
    assert "error_logo: bytes" in image_source

    banner_source = (UI_ROOT / "assets" / "miside_banner.py").read_text(
        encoding="utf-8"
    )
    assert banner_source.startswith("banner_image: bytes =")

    installer_source = (
        UI_ROOT / "tabs" / "plugins" / "installer" / "window.py"
    ).read_text(encoding="utf-8")
    installer_tree = ast.parse(installer_source)
    class_names = {
        node.name for node in installer_tree.body if isinstance(node, ast.ClassDef)
    }
    self_attributes = {
        node.attr
        for node in ast.walk(installer_tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }
    assert "PluginInstallerWindow" in class_names
    assert "InstallMpk" not in class_names
    assert {"pyt", "prog", "installb", "mpk"}.isdisjoint(self_attributes)

def test_vbmeta_patch_caption_is_localized_and_runtime_state_is_boolean() -> None:
    key = "project_pack_partition_window_patch_vbmeta"
    for language_file in sorted(LANGUAGE_DIR.glob("*.json")):
        values = json.loads(language_file.read_text(encoding="utf-8"))
        assert isinstance(values.get(key), str) and values[key].strip()
        assert "VBMeta" in values[key]

    window_source = (
        UI_ROOT / "tabs" / "project" / "pack" / "partition" / "window.py"
    ).read_text(encoding="utf-8")
    assert "PROJECT_PACK_PARTITION_WINDOW_PATCH_VBMETA" in window_source
    assert '"patch_vbmeta": self.spatchvb.get() == 1' in window_source
    assert "Patch VBMeta" not in window_source
    assert "Патч VBMeta" not in window_source

def test_pack_and_unpack_view_specs_localize_display_names() -> None:
    modules = (
        "src.ui.tabs.project.pack.img.view",
        "src.ui.tabs.project.pack.sparse.view",
        "src.ui.tabs.project.pack.dat.view",
        "src.ui.tabs.project.pack.br.view",
        "src.ui.tabs.project.unpack.br.view",
        "src.ui.tabs.project.unpack.dat.view",
        "src.ui.tabs.project.unpack.dat_xz.view",
        "src.ui.tabs.project.unpack.img.view",
        "src.ui.tabs.project.unpack.sparse.view",
        "src.ui.tabs.project.unpack.payload.view",
        "src.ui.tabs.project.unpack.super.view",
        "src.ui.tabs.project.unpack.update_app.view",
        "src.ui.tabs.project.unpack.zst.view",
    )
    english = json.loads((LANGUAGE_DIR / "English.json").read_text(encoding="utf-8"))
    catalog = _Catalog(english)
    for module_name in modules:
        module = importlib.import_module(module_name)
        assert not hasattr(module.SPEC, "display_name")
        technical_value = getattr(module.SPEC, "output_value", None) or getattr(
            module.SPEC, "option_value"
        )
        assert module.get_display_name(catalog) == build_choice_set(
            catalog, (technical_value,)
        ).label_at(0)


def test_mtk_ui_keeps_profile_and_flag_identifiers_separate_from_labels() -> None:
    source = (UI_ROOT / "tabs" / "tools" / "mtk_port_tool" / "panel.py").read_text(
        encoding="utf-8"
    )
    assert "text=name" not in source
    assert "ttk.OptionMenu" not in source
    assert "self._selected_profile_name()" in source
    assert "text=self._flag_label(name)" in source


def test_user_visible_byte_sizes_use_localized_ui_formatters() -> None:
    ui_formatting_source = (UI_ROOT / "common" / "formatting.py").read_text(
        encoding="utf-8"
    )
    assert "def format_bytes" not in ui_formatting_source

    direct_format_calls: list[str] = []
    for source_path in sorted(UI_ROOT.rglob("*.py")):
        source = source_path.read_text(encoding="utf-8")
        if "format_bytes(" in source:
            direct_format_calls.append(str(source_path.relative_to(PROJECT_ROOT)))
    assert direct_format_calls == []


def test_ui_widgets_do_not_embed_literal_technical_choice_lists() -> None:
    violations: list[str] = []
    technical_values = set(TECHNICAL_VALUE_KEYS)
    for source_path in sorted(UI_ROOT.rglob("*.py")):
        if source_path.name == "technical_choices.py":
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
            if call_name == "OptionMenu":
                for argument in node.args[3:]:
                    if (
                        isinstance(argument, ast.Constant)
                        and isinstance(argument.value, str)
                        and argument.value in technical_values
                    ):
                        violations.append(
                            f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                            f"embeds OptionMenu value {argument.value!r}"
                        )
            for keyword in node.keywords:
                if keyword.arg != "values":
                    continue
                try:
                    values = ast.literal_eval(keyword.value)
                except Exception:
                    continue
                if not isinstance(values, (tuple, list)):
                    continue
                embedded = sorted(
                    value
                    for value in values
                    if isinstance(value, str) and value in technical_values
                )
                if embedded:
                    violations.append(
                        f"{source_path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                        f"embeds technical values {embedded!r}"
                    )
    assert violations == []


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
