from __future__ import annotations

from collections.abc import Callable, Mapping

from src.logic.plugins.catalog import PluginCatalogService
from src.logic.plugins.config import PluginConfigService
from src.logic.plugins.editor import PluginEditorService


class PluginManagerController:
    """Application controller for plugin-manager operations."""

    def __init__(self, *, runtime, settings, output, logger=None):
        self.runtime = runtime
        self.settings = settings
        self.logger = logger
        self.output = output
        self.module_manager = runtime.module_manager
        self.config_service = PluginConfigService()
        self.catalog_service = PluginCatalogService(
            module_dir=self.module_manager.module_dir,
            virtual_plugins=self.module_manager.addon_loader.virtual,
        )
        self.editor_service = PluginEditorService(module_dir=self.module_manager.module_dir)

    @property
    def module_dir(self) -> str:
        return self.module_manager.module_dir

    @property
    def output_dir(self) -> str:
        return self.settings.path

    def load_catalog(self):
        return self.catalog_service.load()

    def plugin_config_path(self, plugin_id: str) -> str | None:
        return self.module_manager.plugin_config_path(plugin_id)

    def ensure_background_load(self) -> bool:
        if not self.module_manager.claim_background_load():
            return False
        self.runtime.task_runner.fire_and_forget(self.module_manager.load_plugins_and_notify)
        return True

    def run_plugin(self, plugin_id: str, values: Mapping[str, object]) -> None:
        from src.app.plugins.execution_runtime import build_plugin_execute_runtime_context

        execute_runtime = build_plugin_execute_runtime_context(
            values=values,
            output=self.output,
        )
        self.runtime.task_runner.fire_and_forget(
            lambda: self.module_manager.run(plugin_id, runtime=execute_runtime)
        )

    def uninstall_plugin(self, plugin_id: str, *, on_success: Callable[[object], object]) -> None:
        self.runtime.task_runner.run(
            self.module_manager.uninstall_plugin,
            plugin_id,
            on_success=on_success,
        )

    def export_plugin(self, plugin_id: str) -> None:
        self.runtime.task_runner.fire_and_forget(
            lambda: self.module_manager.export(
                plugin_id,
                output_dir=self.output_dir,
                output=self.output,
            )
        )

    def check_mpk(self, path: str):
        return self.module_manager.check_mpk(path)

    def create_plugin(self, data: dict) -> str:
        return self.module_manager.create_plugin_scaffold(data)

    def is_installed(self, plugin_id: str) -> bool:
        return self.module_manager.is_installed(plugin_id)

    def is_virtual(self, plugin_id: str) -> bool:
        return self.module_manager.is_virtual(plugin_id)

    def get_name(self, plugin_id: str) -> str:
        return self.module_manager.get_name(plugin_id)

    def collect_dependent_plugin_ids(self, plugin_id: str) -> list[str]:
        return self.module_manager.collect_dependent_plugin_ids(plugin_id)

    def prepare_editor_target(self, plugin_id: str):
        return self.editor_service.prepare_target(
            plugin_id,
            is_virtual=self.is_virtual(plugin_id) if plugin_id else False,
        )


__all__ = ['PluginManagerController']
