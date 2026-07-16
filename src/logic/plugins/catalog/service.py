from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from src.logic.plugins.runtime import VirtualPluginInfo


@dataclass(frozen=True)
class PluginCatalogItem:
    plugin_id: str
    display_name: str
    virtual: bool
    icon_path: Path | None = None


@dataclass(frozen=True)
class PluginCatalogIssue:
    plugin_id: str
    message: str


@dataclass(frozen=True)
class PluginCatalogResult:
    items: tuple[PluginCatalogItem, ...]
    issues: tuple[PluginCatalogIssue, ...]


class PluginCatalogService:
    def __init__(
        self,
        *,
        module_dir: str | Path,
        virtual_plugins: Mapping[str, VirtualPluginInfo],
    ) -> None:
        self.module_dir = Path(module_dir)
        self.virtual_plugins = virtual_plugins

    def load(self) -> PluginCatalogResult:
        items = [
            PluginCatalogItem(
                plugin_id=plugin_id,
                display_name=data.name,
                virtual=True,
            )
            for plugin_id, data in sorted(self.virtual_plugins.items())
        ]
        issues: list[PluginCatalogIssue] = []
        if self.module_dir.exists():
            for plugin_path in sorted(
                path for path in self.module_dir.iterdir() if path.is_dir()
            ):
                info_path = plugin_path / 'info.json'
                if not info_path.is_file():
                    issues.append(
                        PluginCatalogIssue(plugin_path.name, 'Missing info.json')
                    )
                    continue
                try:
                    metadata = json.loads(info_path.read_text(encoding='utf-8'))
                except (OSError, json.JSONDecodeError) as exc:
                    issues.append(
                        PluginCatalogIssue(
                            plugin_path.name,
                            f'Invalid info.json: {exc}',
                        )
                    )
                    continue
                if not isinstance(metadata, dict):
                    issues.append(
                        PluginCatalogIssue(
                            plugin_path.name,
                            'Plugin metadata root must be an object',
                        )
                    )
                    continue
                display_name = metadata.get('name')
                if not isinstance(display_name, str) or not display_name.strip():
                    issues.append(
                        PluginCatalogIssue(
                            plugin_path.name,
                            'Plugin name is missing in info.json',
                        )
                    )
                    continue
                icon_path = plugin_path / 'icon'
                items.append(
                    PluginCatalogItem(
                        plugin_id=plugin_path.name,
                        display_name=display_name,
                        virtual=False,
                        icon_path=icon_path if icon_path.is_file() else None,
                    )
                )
        return PluginCatalogResult(items=tuple(items), issues=tuple(issues))


__all__ = [
    'PluginCatalogIssue',
    'PluginCatalogItem',
    'PluginCatalogResult',
    'PluginCatalogService',
]
