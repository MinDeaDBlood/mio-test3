"""Pure Plugin Store catalog filtering helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from src.ui.tabs.plugins.store.contracts import PluginCatalogItemProtocol


def normalize_search_term(value: object) -> str:
    """Return the canonical case insensitive store search term."""
    return str(value or "").strip().lower()


def build_plugin_name_index(
    items: Iterable[PluginCatalogItemProtocol],
) -> dict[str, str]:
    """Build a plugin id to normalized plugin name index."""
    return {item.plugin_id: item.name.lower() for item in items}


def is_plugin_visible(
    plugin_id: str,
    *,
    name_index: Mapping[str, str],
    search_term: str,
) -> bool:
    """Return whether a catalog row should be visible for the current search."""
    term = normalize_search_term(search_term)
    if not term:
        return True
    return term in name_index.get(plugin_id, "")


def build_catalog_visibility(
    plugin_ids: Iterable[str],
    items: Iterable[PluginCatalogItemProtocol],
    search_term: object,
) -> dict[str, bool]:
    """Map plugin ids to their desired visible state for the search term."""
    normalized_term = normalize_search_term(search_term)
    name_index = build_plugin_name_index(items)
    return {
        plugin_id: is_plugin_visible(
            plugin_id,
            name_index=name_index,
            search_term=normalized_term,
        )
        for plugin_id in plugin_ids
    }


__all__ = [
    "build_catalog_visibility",
    "build_plugin_name_index",
    "is_plugin_visible",
    "normalize_search_term",
]
