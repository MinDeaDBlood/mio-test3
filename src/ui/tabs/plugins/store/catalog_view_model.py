"""Immutable view models for Plugin Store catalog cards."""

from __future__ import annotations

from dataclasses import dataclass

from src.ui.common.byte_size import format_localized_byte_size
from src.ui.tabs.plugins.store.contracts import PluginCatalogItemProtocol
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins.store import keys

PLUGIN_STORE_ACTION_BUTTON_MIN_WIDTH = 12


@dataclass(frozen=True, slots=True)
class PluginStoreMetadataViewModel:
    author_label: str
    version_label: str
    size_label: str
    description: str


@dataclass(frozen=True, slots=True)
class PluginStoreActionViewModel:
    plugin_id: str
    size_bytes: int
    files: tuple[str, ...]
    dependencies: tuple[str, ...]
    download_args: tuple[tuple[str, ...], int, str, tuple[str, ...]]
    button_width: int
    install_text: str
    uninstall_text: str


@dataclass(frozen=True, slots=True)
class PluginStoreCardViewModel:
    plugin_id: str
    title: str
    metadata: PluginStoreMetadataViewModel
    actions: PluginStoreActionViewModel


def resolve_store_button_width(raw_value: object) -> int:
    """Return a positive button width or reject invalid UI configuration."""
    if not isinstance(raw_value, (int, float, str, bytes, bytearray)):
        raise ValueError(f"Invalid Plugin Store button width: {raw_value!r}")
    try:
        width = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid Plugin Store button width: {raw_value!r}") from exc
    if width <= 0:
        raise ValueError(f"Plugin Store button width must be positive: {width}")
    return width


def build_metadata_view_model(
    item: PluginCatalogItemProtocol,
    *,
    texts: LocalizationCatalog,
) -> PluginStoreMetadataViewModel:
    """Build localized metadata labels for one validated catalog item."""
    return PluginStoreMetadataViewModel(
        author_label=f"{texts.resolve_required_ui_text(keys.CATALOG_AUTHOR_LABEL)} {item.author}".strip(),
        version_label=f"{texts.resolve_required_ui_text(keys.CATALOG_VERSION_LABEL)} {item.version}".strip(),
        size_label=(
            f"{texts.resolve_required_ui_text(keys.CATALOG_SIZE_LABEL)} "
            f"{format_localized_byte_size(item.size_bytes, texts=texts)}"
        ).strip(),
        description=item.description,
    )


def build_action_view_model(
    item: PluginCatalogItemProtocol,
    *,
    texts: LocalizationCatalog,
    button_width: int,
) -> PluginStoreActionViewModel:
    """Build action and download data for one validated catalog item."""
    return PluginStoreActionViewModel(
        plugin_id=item.plugin_id,
        size_bytes=item.size_bytes,
        files=item.files,
        dependencies=item.dependencies,
        download_args=(item.files, item.size_bytes, item.plugin_id, item.dependencies),
        button_width=resolve_store_button_width(button_width),
        install_text=texts.resolve_required_ui_text(
            keys.PLUGINS_STORE_CATALOG_VIEW_MODEL_INSTALL
        ),
        uninstall_text=texts.resolve_required_ui_text(
            keys.PLUGINS_STORE_CATALOG_VIEW_MODEL_UNINSTALL
        ),
    )


def build_card_view_model(
    item: PluginCatalogItemProtocol,
    *,
    texts: LocalizationCatalog,
    button_width: int,
) -> PluginStoreCardViewModel:
    """Convert one validated catalog item into its presentation model."""
    return PluginStoreCardViewModel(
        plugin_id=item.plugin_id,
        title=item.name,
        metadata=build_metadata_view_model(item, texts=texts),
        actions=build_action_view_model(item, texts=texts, button_width=button_width),
    )


__all__ = [
    "PluginStoreActionViewModel",
    "PluginStoreCardViewModel",
    "PluginStoreMetadataViewModel",
    "build_action_view_model",
    "build_card_view_model",
    "build_metadata_view_model",
    "PLUGIN_STORE_ACTION_BUTTON_MIN_WIDTH",
    "resolve_store_button_width",
]
