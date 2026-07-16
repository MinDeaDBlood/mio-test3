"""Validated domain models for the Plugin Store repository catalog."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol


class PluginCatalogItemProtocol(Protocol):
    @property
    def plugin_id(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...
    @property
    def author(self) -> str: ...
    @property
    def version(self) -> str: ...
    @property
    def size_bytes(self) -> int: ...
    @property
    def dependencies(self) -> tuple[str, ...]: ...
    @property
    def systems(self) -> str: ...
    @property
    def architecture(self) -> str: ...
    @property
    def files(self) -> tuple[str, ...]: ...


class PluginCatalogValidationError(ValueError):
    """Raised when a repository payload does not match the catalog contract."""


def _require_text(value: object, *, field_name: str, item_index: int) -> str:
    if not isinstance(value, str):
        raise PluginCatalogValidationError(
            f"Plugin catalog item {item_index} field {field_name!r} must be a string."
        )
    text = value.strip()
    if not text:
        raise PluginCatalogValidationError(
            f"Plugin catalog item {item_index} has an empty {field_name!r} field."
        )
    return text


def _optional_text(
    value: object,
    *,
    field_name: str,
    item_index: int,
    default: str = "",
) -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise PluginCatalogValidationError(
            f"Plugin catalog item {item_index} field {field_name!r} must be a string."
        )
    return value.strip()


def _string_tuple(
    value: object, *, field_name: str, item_index: int
) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raw_values: Sequence[object] = value.split()
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        raw_values = value
    else:
        raise PluginCatalogValidationError(
            f"Plugin catalog item {item_index} field {field_name!r} must be a string or a sequence of strings."
        )

    result: list[str] = []
    seen: set[str] = set()
    for entry in raw_values:
        if not isinstance(entry, str):
            raise PluginCatalogValidationError(
                f"Plugin catalog item {item_index} field {field_name!r} must contain only strings."
            )
        text = entry.strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return tuple(result)


def _non_negative_int(value: object, *, field_name: str, item_index: int) -> int:
    if isinstance(value, bool):
        raise PluginCatalogValidationError(
            f"Plugin catalog item {item_index} field {field_name!r} must be an integer."
        )
    if value is None:
        normalized = 0
    elif isinstance(value, int):
        normalized = value
    elif isinstance(value, str) and value.strip().isdigit():
        normalized = int(value.strip())
    else:
        raise PluginCatalogValidationError(
            f"Plugin catalog item {item_index} field {field_name!r} must be an integer."
        )
    if normalized < 0:
        raise PluginCatalogValidationError(
            f"Plugin catalog item {item_index} field {field_name!r} cannot be negative."
        )
    return normalized


@dataclass(frozen=True, slots=True)
class PluginCatalogItem:
    """One normalized plugin entry from the repository catalog."""

    plugin_id: str
    name: str
    description: str
    author: str
    version: str
    size_bytes: int
    dependencies: tuple[str, ...]
    systems: str
    architecture: str
    files: tuple[str, ...]

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
        *,
        item_index: int = 0,
    ) -> PluginCatalogItem:
        plugin_id = _require_text(
            value.get("id"), field_name="id", item_index=item_index
        )
        name = (
            _optional_text(
                value.get("name"),
                field_name="name",
                item_index=item_index,
                default=plugin_id,
            )
            or plugin_id
        )
        return cls(
            plugin_id=plugin_id,
            name=name,
            description=_optional_text(
                value.get("desc"), field_name="desc", item_index=item_index
            ),
            author=_optional_text(
                value.get("author"), field_name="author", item_index=item_index
            ),
            version=_optional_text(
                value.get("version"), field_name="version", item_index=item_index
            ),
            size_bytes=_non_negative_int(
                value.get("size"), field_name="size", item_index=item_index
            ),
            dependencies=_string_tuple(
                value.get("depend"), field_name="depend", item_index=item_index
            ),
            systems=_optional_text(
                value.get("system"),
                field_name="system",
                item_index=item_index,
                default="all",
            )
            or "all",
            architecture=_optional_text(
                value.get("arch"),
                field_name="arch",
                item_index=item_index,
                default="all",
            )
            or "all",
            files=_string_tuple(
                value.get("files"), field_name="files", item_index=item_index
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return the canonical JSON representation used by the cache file."""
        return {
            "name": self.name,
            "desc": self.description,
            "author": self.author,
            "version": self.version,
            "size": self.size_bytes,
            "id": self.plugin_id,
            "depend": list(self.dependencies),
            "system": self.systems,
            "arch": self.architecture,
            "files": list(self.files),
        }


def parse_plugin_catalog(payload: object) -> tuple[PluginCatalogItem, ...]:
    """Validate an untrusted JSON payload and return immutable catalog items."""
    if not isinstance(payload, list):
        raise PluginCatalogValidationError("Plugin catalog root must be a JSON array.")

    items: list[PluginCatalogItem] = []
    seen_ids: set[str] = set()
    for item_index, raw_item in enumerate(payload):
        if not isinstance(raw_item, Mapping):
            raise PluginCatalogValidationError(
                f"Plugin catalog item {item_index} must be a JSON object."
            )
        item = PluginCatalogItem.from_mapping(raw_item, item_index=item_index)
        if item.plugin_id in seen_ids:
            raise PluginCatalogValidationError(
                f"Plugin catalog contains duplicate id {item.plugin_id!r}."
            )
        seen_ids.add(item.plugin_id)
        items.append(item)
    return tuple(items)


__all__ = [
    "PluginCatalogItem",
    "PluginCatalogItemProtocol",
    "PluginCatalogValidationError",
    "parse_plugin_catalog",
]
