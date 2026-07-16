from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Protocol

from src.logic.plugins.runtime import VirtualPluginInfo


class VirtualPluginRegistryProtocol(Protocol):
    @property
    def virtual(self) -> Mapping[str, VirtualPluginInfo]: ...


class PluginMetadataService:
    """Read validated plugin metadata without exposing untyped JSON values."""

    def __init__(
        self,
        *,
        module_dir: str,
        addon_loader: VirtualPluginRegistryProtocol,
        logger: logging.Logger | None = None,
    ) -> None:
        self.module_dir = module_dir
        self.addon_loader = addon_loader
        self.logger = logger or logging.getLogger(__name__)

    def is_installed(self, plugin_id: str) -> bool:
        path = os.path.join(self.module_dir, plugin_id)
        return os.path.isdir(path) and os.path.exists(
            os.path.join(path, 'info.json')
        )

    def is_virtual(self, plugin_id: str) -> bool:
        return plugin_id in self.addon_loader.virtual

    def read_metadata(self, plugin_id: str) -> Mapping[str, object]:
        info_file = os.path.join(self.module_dir, plugin_id, 'info.json')
        if not os.path.exists(info_file):
            return {}
        try:
            with open(info_file, 'r', encoding='UTF-8') as stream:
                payload = json.load(stream)
        except json.JSONDecodeError:
            self.logger.error(
                'Error decoding JSON from %s for plugin %s',
                info_file,
                plugin_id,
            )
            return {}
        except OSError as exc:
            self.logger.error(
                'Error reading info file %s for plugin %s: %s',
                info_file,
                plugin_id,
                exc,
            )
            return {}
        if not isinstance(payload, dict):
            self.logger.error(
                'Plugin metadata root in %s for plugin %s is not an object',
                info_file,
                plugin_id,
            )
            return {}
        return payload

    def get_info(
        self,
        plugin_id: str,
        item: str,
        default: object = None,
    ) -> object:
        return self.read_metadata(plugin_id).get(item, default)

    def get_text(self, plugin_id: str, item: str, default: str = '') -> str:
        value = self.get_info(plugin_id, item, default)
        if isinstance(value, str):
            return value
        self.logger.warning(
            'Plugin metadata field %s for %s must be a string',
            item,
            plugin_id,
        )
        return default

    def get_name(self, plugin_id: str) -> str:
        virtual_info = self.addon_loader.virtual.get(plugin_id)
        if virtual_info is not None:
            return virtual_info.name
        return self.get_text(plugin_id, 'name', plugin_id) or plugin_id

    def list_packages(self) -> tuple[str, ...]:
        if not os.path.isdir(self.module_dir):
            return ()
        return tuple(
            plugin_id
            for plugin_id in os.listdir(self.module_dir)
            if self.is_installed(plugin_id)
            and os.path.isdir(os.path.join(self.module_dir, plugin_id))
        )


__all__ = [
    'PluginMetadataService',
    'VirtualPluginRegistryProtocol',
]
