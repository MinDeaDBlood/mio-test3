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


from dataclasses import fields

import pytest

from tests.support.paths import PROJECT_ROOT


from src.app.localization_runtime import LangUtils
from src.logic.plugins.store_models import (
    PluginCatalogItem,
    PluginCatalogValidationError,
    parse_plugin_catalog,
)
from src.ui.tabs.plugins.store.catalog_card_widgets import PluginStoreCardWidgets
from src.ui.tabs.plugins.store.catalog_filter import (
    build_catalog_visibility,
    build_plugin_name_index,
    is_plugin_visible,
    normalize_search_term,
)
from src.ui.tabs.plugins.store.catalog_view_model import (
    build_action_view_model,
    build_card_view_model,
    resolve_store_button_width,
)
from tests.support.plugin_catalog import plugin_item


def _texts() -> LangUtils:
    texts = LangUtils()
    texts.load_map(
        {
            "plugins_store_catalog_view_model_author_label": "Author",
            "plugins_store_catalog_view_model_version_label": "Version",
            "plugins_store_catalog_view_model_image_size_label": "Size",
            "plugins_store_catalog_view_model_install": "Install",
            "plugins_store_catalog_view_model_uninstall": "Uninstall",
        }
    )
    return texts


def test_catalog_filter_is_pure_and_deterministic() -> None:
    items = (
        plugin_item("demo", name="Demo Plugin"),
        plugin_item("other", name="Other Plugin"),
    )
    assert normalize_search_term("  DEMO  ") == "demo"
    assert build_plugin_name_index(items) == {
        "demo": "demo plugin",
        "other": "other plugin",
    }
    assert (
        is_plugin_visible(
            "demo",
            name_index={"demo": "demo plugin"},
            search_term="plug",
        )
        is True
    )
    assert (
        is_plugin_visible(
            "demo",
            name_index={"demo": "demo plugin"},
            search_term="other",
        )
        is False
    )
    assert build_catalog_visibility(("demo", "other"), items, "demo") == {
        "demo": True,
        "other": False,
    }
    assert build_catalog_visibility(("demo", "other"), items, "") == {
        "demo": True,
        "other": True,
    }


def test_catalog_model_validates_and_normalizes_repository_payload() -> None:
    items = parse_plugin_catalog(
        [
            {
                "id": "demo",
                "name": " Demo Plugin ",
                "desc": "Description",
                "author": "Author",
                "version": "1.0",
                "size": 128,
                "depend": ["base", "", "base", "extra"],
                "system": "all",
                "arch": "all",
                "files": ["demo.zip", "", "demo.zip"],
            }
        ]
    )
    assert items == (
        PluginCatalogItem(
            plugin_id="demo",
            name="Demo Plugin",
            description="Description",
            author="Author",
            version="1.0",
            size_bytes=128,
            dependencies=("base", "extra"),
            systems="all",
            architecture="all",
            files=("demo.zip",),
        ),
    )
    assert items[0].to_mapping()["id"] == "demo"

    with pytest.raises(PluginCatalogValidationError, match="JSON array"):
        parse_plugin_catalog({"id": "demo"})
    with pytest.raises(PluginCatalogValidationError, match="duplicate id"):
        parse_plugin_catalog([{"id": "demo"}, {"id": "demo"}])
    with pytest.raises(PluginCatalogValidationError, match="must contain only strings"):
        parse_plugin_catalog([{"id": "demo", "files": [7]}])
    with pytest.raises(PluginCatalogValidationError, match="must be an integer"):
        parse_plugin_catalog([{"id": "demo", "size": 1.5}])
    with pytest.raises(PluginCatalogValidationError, match="cannot be negative"):
        parse_plugin_catalog([{"id": "demo", "size": -1}])


def test_catalog_view_model_consumes_validated_model() -> None:
    item = plugin_item(
        "demo",
        name="Demo Plugin",
        description="Description",
        author="Author",
        version="1.0",
        size_bytes=128,
        dependencies=("base", "extra"),
        files=("demo.zip",),
    )
    assert resolve_store_button_width("18") == 18
    with pytest.raises(ValueError):
        resolve_store_button_width("bad")
    with pytest.raises(ValueError):
        resolve_store_button_width("-2")

    action = build_action_view_model(item, texts=_texts(), button_width=12)
    assert action.plugin_id == "demo"
    assert action.files == ("demo.zip",)
    assert action.dependencies == ("base", "extra")
    assert action.download_args == (("demo.zip",), 128, "demo", ("base", "extra"))

    card = build_card_view_model(item, texts=_texts(), button_width=12)
    assert card.plugin_id == "demo"
    assert card.title == "Demo Plugin"
    assert card.metadata.description == "Description"
    assert card.actions.files == ("demo.zip",)


def test_card_widget_boundary_dataclass_contract() -> None:
    assert [field.name for field in fields(PluginStoreCardWidgets)] == [
        "frame",
        "install_button",
        "uninstall_button",
    ]


def test_catalog_source_contracts_keep_validation_out_of_ui_cards() -> None:
    cards_source = (PROJECT_ROOT / "src/ui/tabs/plugins/store/cards.py").read_text(
        encoding="utf-8"
    )
    view_model_source = (
        PROJECT_ROOT / "src/ui/tabs/plugins/store/catalog_view_model.py"
    ).read_text(encoding="utf-8")
    service_source = (PROJECT_ROOT / "src/logic/plugins/store_service.py").read_text(
        encoding="utf-8"
    )
    model_source = (PROJECT_ROOT / "src/logic/plugins/store_models.py").read_text(
        encoding="utf-8"
    )

    assert "build_card_view_model" in cards_source
    assert "PluginCatalogItem" in view_model_source
    assert "parse_plugin_catalog" in service_source
    assert "PluginCatalogValidationError" in model_source
    for token in (
        "item.get('author'",
        "item.get('version'",
        "item.get('files'",
        "item.get('depend'",
        "dict[str, Any]",
    ):
        assert token not in cards_source
        assert token not in view_model_source


if __name__ == "__main__":
    test_catalog_filter_is_pure_and_deterministic()
    test_catalog_model_validates_and_normalizes_repository_payload()
    test_catalog_view_model_consumes_validated_model()
    test_card_widget_boundary_dataclass_contract()
    test_catalog_source_contracts_keep_validation_out_of_ui_cards()
    print("PLUGIN_STORE_CATALOG_VIEW_MODEL_TESTS_OK")
