from __future__ import annotations

import logging
import os

from src.core import imp
from src.logic.plugins.runtime import Entry, loader
from src.logic.common.service_output import build_service_output
from src.logic.plugins.events import PluginStateChangedEvent, plugin_event_bus
from src.logic.plugins.execute.service import PluginExecuteService
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

    def load_plugins_and_notify(self) -> None:
        try:
            self.load_plugins()
        # Plugin loading executes third party code. The broad boundary prevents one
        # plugin from terminating the background loader.
        except Exception:
            logging.exception("ModuleManager background plugin load failed")
        else:
            try:
                self.notify_plugin_state_changed()
            # Event subscribers can belong to third party plugins. Keep this isolation
            # boundary broad so a subscriber cannot terminate the loader thread.
            except Exception:
                logging.exception("ModuleManager background plugin refresh failed")

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

    def _execute_service(self, runtime) -> PluginExecuteService:
        return PluginExecuteService(
            module_dir=self.module_dir,
            addon_loader=self.addon_loader,
            addon_entries=self.addon_entries,
            is_virtual=self.is_virtual,
            get_name=self.get_name,
            register_plugin=self.register_plugin,
            runtime=runtime,
            logger=self.logger,
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

    def register_plugin(self, plugin_id: str):
        script_path = os.path.join(self.module_dir, plugin_id)
        main_py_path = os.path.join(script_path, "main.py")
        if os.path.exists(main_py_path) and imp:
            try:
                module = imp.load_source(plugin_id, main_py_path)
                if hasattr(module, "entrances"):
                    for entry, func in module.entrances.items():
                        self.addon_loader.register(plugin_id, entry, func)
                elif hasattr(module, "main"):
                    self.addon_loader.register(
                        plugin_id, self.addon_entries.main, module.main
                    )
                else:
                    logging.warning(
                        "Plugin entry point is missing: plugin_id=%s; name=%s",
                        plugin_id,
                        self.get_name(plugin_id),
                    )
            # Importing a plugin executes arbitrary third party Python code. This is
            # an intentional isolation boundary, not generic application error handling.
            except Exception:
                logging.exception(
                    "plugins.module_manager.register_failed: plugin_id=%s; name=%s; path=%s",
                    plugin_id,
                    self.get_name(plugin_id),
                    main_py_path,
                )

    def load_plugins(self):
        os.makedirs(self.module_dir, exist_ok=True)
        for plugin_id in self.list_packages():
            self.register_plugin(plugin_id)

    def get_info(self, plugin_id: str, item: str, default=None):
        return self._metadata_service().get_info(plugin_id, item, default)

    def plugin_config_path(self, plugin_id: str) -> str | None:
        if not plugin_id:
            return None
        config_path = os.path.join(self.module_dir, plugin_id, "main.json")
        return config_path if os.path.isfile(config_path) else None

    def run(self, plugin_id=None, *, runtime) -> int:
        result = self._execute_service(runtime).run(plugin_id)
        if (
            result == 0
            and plugin_id
            and not self.is_installed(plugin_id)
            and not self.is_virtual(plugin_id)
        ):
            self.request_plugin_list_refresh()
        return result

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
