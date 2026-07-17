from __future__ import annotations

from collections.abc import Callable, Mapping
import logging

from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity
from src.logic.plugins.execution_plan import plan_plugin_execution
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
        self.plugin_gateway = runtime.plugin_gateway
        self.config_service = PluginConfigService()
        self.catalog_service = PluginCatalogService(
            module_dir=self.plugin_gateway.module_dir,
            virtual_plugins=self.plugin_gateway.virtual_plugins,
        )
        self.editor_service = PluginEditorService(module_dir=self.plugin_gateway.module_dir)

    @property
    def module_dir(self) -> str:
        return self.plugin_gateway.module_dir

    @property
    def output_dir(self) -> str:
        return self.settings.path

    def load_catalog(self):
        return self.catalog_service.load()

    def plugin_config_path(self, plugin_id: str) -> str | None:
        return self.plugin_gateway.plugin_config_path(plugin_id)

    def ensure_background_load(self) -> bool:
        if not self.plugin_gateway.claim_background_load():
            return False
        self.runtime.task_runner.fire_and_forget(self.plugin_gateway.load_plugins_and_notify)
        return True

    def run_plugin(self, plugin_id: str, values: Mapping[str, object]) -> None:
        from src.app.plugins.execution_runtime import build_plugin_execution_runtime

        execution_runtime = build_plugin_execution_runtime(
            values=values,
            output=self.output,
        )
        self.runtime.task_runner.fire_and_forget(
            self._execute_plugin,
            plugin_id,
            execution_runtime,
        )

    def _execute_plugin(self, plugin_id: str, execution_runtime) -> int:
        inspection = self.plugin_gateway.inspect_execution(plugin_id)
        plan = plan_plugin_execution(
            plugin_id,
            project_name=execution_runtime.project_name,
            inspection=inspection,
        )
        logging.getLogger(__name__).info(
            "plugin.execution_planned: plugin_id=%s entry_kind=%s entry_path=%s error=%s",
            plugin_id,
            plan.entry_kind.value if plan.entry_kind is not None else "none",
            plan.entry_path,
            plan.error_code or "none",
        )
        if not plan.can_execute:
            execution_runtime.output.log_and_report(
                message(plan.error_code, plan.error_default, **plan.error_params),
                severity=OutputSeverity.ERROR,
            )
            return 1
        return self.plugin_gateway.execute_planned(
            plugin_id,
            entry_kind=plan.entry_kind.value,
            entry_path=plan.entry_path,
            project_work_path=execution_runtime.project_work_path,
            project_output_path=execution_runtime.project_output_path,
            tool_bin=execution_runtime.tool_bin,
            tool_version=execution_runtime.tool_version,
            language=execution_runtime.language,
            temp_path=execution_runtime.temp_path,
            module_exec=execution_runtime.module_exec,
            values=execution_runtime.values,
        )

    def uninstall_plugin(self, plugin_id: str, *, on_success: Callable[[object], object]) -> None:
        self.runtime.task_runner.run(
            self.plugin_gateway.uninstall,
            plugin_id,
            on_success=on_success,
        )

    def export_plugin(self, plugin_id: str) -> None:
        self.runtime.task_runner.fire_and_forget(
            lambda: self.plugin_gateway.export(
                plugin_id,
                output_dir=self.output_dir,
                output=self.output,
            )
        )

    def check_mpk(self, path: str):
        return self.plugin_gateway.check_package(path)

    def create_plugin(self, data: dict) -> str:
        return self.plugin_gateway.create_scaffold(data)

    def is_installed(self, plugin_id: str) -> bool:
        return self.plugin_gateway.is_installed(plugin_id)

    def is_virtual(self, plugin_id: str) -> bool:
        return self.plugin_gateway.is_virtual(plugin_id)

    def get_name(self, plugin_id: str) -> str:
        return self.plugin_gateway.get_name(plugin_id)

    def collect_dependent_plugin_ids(self, plugin_id: str) -> list[str]:
        return self.plugin_gateway.collect_dependent_plugin_ids(plugin_id)

    def prepare_editor_target(self, plugin_id: str):
        return self.editor_service.prepare_target(
            plugin_id,
            is_virtual=self.is_virtual(plugin_id) if plugin_id else False,
        )


__all__ = ['PluginManagerController']
