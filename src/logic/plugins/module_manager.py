from __future__ import annotations

import logging
import os

from src.logic.plugins.runtime import Entry, loader
from src.logic.common.service_output import build_service_output
from src.logic.plugins.events import PluginStateChangedEvent, plugin_event_bus
from src.logic.plugins.export.service import PluginExportService
from src.logic.plugins.install.service import PluginInstallService
from src.logic.plugins.metadata.service import PluginMetadataService
from src.logic.plugins.scaffold.service import PluginScaffoldService
from src.logic.plugins.uninstall.service import PluginUninstallService


class ModuleManager:
    def __init__(self, *, module_dir: str | os.PathLike[str]):
        self.module_dir = os.fspath(module_dir)
        os.makedirs(self.module_dir, exist_ok=True)
        self.addon_loader = loader
        self.addon_entries = Entry
        self._load_thread_started = False
        self.logger = logging.getLogger(__name__)

    def claim_background_load(self) -> bool:
        if self._load_thread_started:
            return False
        self._load_thread_started = True
        return True

    def request_plugin_list_refresh(self):
        plugin_event_bus.publish(
            PluginStateChangedEvent(
                plugin_id=None, refresh_manager=True, refresh_store=True
            )
        )
        return True

    def update_store_plugin_state(self, plugin_id: str):
        plugin_event_bus.publish(
            PluginStateChangedEvent(
                plugin_id=plugin_id, refresh_manager=False, refresh_store=True
            )
        )
        return True

    def notify_plugin_state_changed(self, plugin_id: str | None = None):
        plugin_event_bus.publish(
            PluginStateChangedEvent(
                plugin_id=plugin_id, refresh_manager=True, refresh_store=True
            )
        )

    def _metadata_service(self) -> PluginMetadataService:
        return PluginMetadataService(
            module_dir=self.module_dir, addon_loader=self.addon_loader, logger=self.logger
        )

    def _install_service(self) -> PluginInstallService:
        return PluginInstallService(
            module_dir=self.module_dir,
            notify_plugin_state_changed=self.notify_plugin_state_changed,
            logger=self.logger,
        )

    def _uninstall_service(self) -> PluginUninstallService:
        return PluginUninstallService(
            module_dir=self.module_dir,
            list_packages=self.list_packages,
            get_info=self.get_info,
            get_name=self.get_name,
            is_virtual=self.is_virtual,
            notify_plugin_state_changed=self.notify_plugin_state_changed,
            logger=self.logger,
            output=build_service_output(),
        )

    def _export_service(self, output_dir: str, *, output=None) -> PluginExportService:
        return PluginExportService(
            module_dir=self.module_dir,
            get_name=self.get_name,
            is_virtual=self.is_virtual,
            output_dir=output_dir,
            output=output,
            logger=self.logger,
        )

    def _scaffold_service(self) -> PluginScaffoldService:
        return PluginScaffoldService(
            module_dir=self.module_dir,
            notify_plugin_state_changed=self.notify_plugin_state_changed,
        )

    def collect_dependent_plugin_ids(self, plugin_id: str) -> list[str]:
        return self._uninstall_service().collect_dependent_plugin_ids(plugin_id)

    def uninstall_plugin(
        self, plugin_id: str, *, include_dependents: bool = True
    ) -> tuple[bool, str, list[str]]:
        return self._uninstall_service().uninstall_plugin(
            plugin_id, include_dependents=include_dependents
        )

    def is_installed(self, plugin_id) -> bool:
        return self._metadata_service().is_installed(plugin_id)

    def is_virtual(self, plugin_id) -> bool:
        return self._metadata_service().is_virtual(plugin_id)

    def get_name(self, plugin_id) -> str:
        return self._metadata_service().get_name(plugin_id)

    def list_packages(self):
        return self._metadata_service().list_packages()

    def get_info(self, plugin_id: str, item: str, default=None):
        return self._metadata_service().get_info(plugin_id, item, default)

    def plugin_config_path(self, plugin_id: str) -> str | None:
        if not plugin_id:
            return None
        config_path = os.path.join(self.module_dir, plugin_id, "main.json")
        return config_path if os.path.isfile(config_path) else None

    @staticmethod
    def check_mpk(mpk):
        return PluginInstallService.check_mpk(mpk)

    def install(self, mpk_path):
        return self._install_service().install(mpk_path)

    def export(self, plugin_id: str, *, output_dir: str, output=None):
        if not plugin_id:
            return 1
        return self._export_service(output_dir, output=output).export(plugin_id)

    def create_plugin_scaffold(self, data: dict):
        return self._scaffold_service().create_plugin_scaffold(data)
