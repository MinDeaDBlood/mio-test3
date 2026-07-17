from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.core import imp
from src.platform.operation_logging import operation_context
from src.platform.plugins.execution import PluginExecutionAdapter

logger = logging.getLogger(__name__)


class PluginGateway:
    """Platform adapter for plugin storage, loading and external execution."""

    def __init__(self, manager: Any) -> None:
        self._manager = manager

    @property
    def module_dir(self) -> str:
        return str(self._manager.module_dir)

    @property
    def virtual_plugins(self) -> Mapping[str, object]:
        return self._manager.addon_loader.virtual

    def request_plugin_list_refresh(self) -> bool:
        return bool(self._manager.request_plugin_list_refresh())

    def claim_background_load(self) -> bool:
        return bool(self._manager.claim_background_load())

    def load_plugins_and_notify(self) -> None:
        with operation_context("plugin.load_all", module_dir=self.module_dir):
            logger.info("plugin.load_all.started: module_dir=%s", self.module_dir)
            try:
                self._load_plugins()
            except Exception:
                logger.exception(
                    "plugin.load_all.failed: stage=load module_dir=%s",
                    self.module_dir,
                )
                return
            try:
                self._manager.notify_plugin_state_changed()
            except Exception:
                logger.exception(
                    "plugin.load_all.failed: stage=notify module_dir=%s",
                    self.module_dir,
                )
                return
            logger.info("plugin.load_all.completed: module_dir=%s", self.module_dir)

    def _load_plugins(self) -> None:
        module_dir = Path(self.module_dir)
        module_dir.mkdir(parents=True, exist_ok=True)
        plugin_ids = tuple(self._manager.list_packages())
        logger.info(
            "plugin.discovery.completed: module_dir=%s count=%s plugin_ids=%s",
            module_dir,
            len(plugin_ids),
            plugin_ids,
        )
        for plugin_id in plugin_ids:
            self._register_plugin(plugin_id)

    def _register_plugin(self, plugin_id: str) -> None:
        main_py_path = Path(self.module_dir) / plugin_id / "main.py"
        if not main_py_path.is_file():
            logger.debug(
                "plugin.registration.skipped: plugin_id=%s reason=python_entry_missing",
                plugin_id,
            )
            return
        if not imp:
            logger.error(
                "plugin.registration.failed: plugin_id=%s reason=importer_unavailable",
                plugin_id,
            )
            return

        with operation_context(
            "plugin.register_python",
            plugin_id=plugin_id,
            entry_path=str(main_py_path),
        ):
            logger.info(
                "plugin.registration.started: plugin_id=%s path=%s",
                plugin_id,
                main_py_path,
            )
            try:
                module = imp.load_source(plugin_id, str(main_py_path))
                if hasattr(module, "entrances"):
                    entries = module.entrances
                    logger.info(
                        "plugin.registration.entries: plugin_id=%s count=%s",
                        plugin_id,
                        len(entries),
                    )
                    for entry, func in entries.items():
                        self._manager.addon_loader.register(plugin_id, entry, func)
                elif hasattr(module, "main"):
                    self._manager.addon_loader.register(
                        plugin_id,
                        self._manager.addon_entries.main,
                        module.main,
                    )
                else:
                    logger.warning(
                        "plugin.registration.entry_missing: plugin_id=%s name=%s path=%s",
                        plugin_id,
                        self.get_name(plugin_id),
                        main_py_path,
                    )
                    return
            except Exception:
                logger.exception(
                    "plugin.registration.failed: plugin_id=%s name=%s path=%s",
                    plugin_id,
                    self.get_name(plugin_id),
                    main_py_path,
                )
                return
            logger.info("plugin.registration.completed: plugin_id=%s", plugin_id)

    def inspect_execution(self, plugin_id: str) -> Mapping[str, object]:
        """Read executable plugin state without deciding whether it may run."""
        plugin_path = Path(self.module_dir) / plugin_id
        virtual = self.is_virtual(plugin_id)
        inspection: dict[str, object] = {
            "plugin_name": self.get_name(plugin_id),
            "virtual": virtual,
            "plugin_exists": plugin_path.is_dir(),
            "manifest_state": "not-required" if virtual else "missing",
            "dependencies": (),
            "missing_dependencies": (),
            "python_entry_path": "",
            "shell_entry_path": "",
        }
        if virtual:
            logger.info(
                "plugin.inspection.completed: plugin_id=%s virtual=true",
                plugin_id,
            )
            return inspection

        python_entry = plugin_path / "main.py"
        shell_entry = plugin_path / "main.sh"
        inspection["python_entry_path"] = str(python_entry) if python_entry.is_file() else ""
        inspection["shell_entry_path"] = str(shell_entry) if shell_entry.is_file() else ""

        manifest_path = plugin_path / "info.json"
        if manifest_path.is_file():
            try:
                logger.debug(
                    "plugin.manifest.read_started: plugin_id=%s path=%s",
                    plugin_id,
                    manifest_path,
                )
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                inspection["manifest_state"] = "invalid"
                logger.exception(
                    "plugin.manifest.invalid: plugin_id=%s path=%s",
                    plugin_id,
                    manifest_path,
                )
            except OSError:
                inspection["manifest_state"] = "unreadable"
                logger.exception(
                    "plugin.manifest.read_failed: plugin_id=%s path=%s",
                    plugin_id,
                    manifest_path,
                )
            else:
                dependencies = tuple(str(data.get("depend", "")).split())
                missing_dependencies = tuple(
                    dependency
                    for dependency in dependencies
                    if dependency and not (Path(self.module_dir) / dependency).exists()
                )
                inspection["manifest_state"] = "valid"
                inspection["dependencies"] = dependencies
                inspection["missing_dependencies"] = missing_dependencies
        logger.info(
            "plugin.inspection.completed: plugin_id=%s exists=%s manifest=%s "
            "python=%s shell=%s dependencies=%s missing_dependencies=%s",
            plugin_id,
            inspection["plugin_exists"],
            inspection["manifest_state"],
            bool(inspection["python_entry_path"]),
            bool(inspection["shell_entry_path"]),
            inspection["dependencies"],
            inspection["missing_dependencies"],
        )
        return inspection

    def execute_planned(
        self,
        plugin_id: str,
        *,
        entry_kind: str,
        entry_path: str,
        project_work_path: str,
        project_output_path: str,
        tool_bin: str,
        tool_version: str,
        language: str,
        temp_path: str,
        module_exec: str,
        values: Mapping[str, object],
    ) -> int:
        adapter = PluginExecutionAdapter(
            module_dir=self.module_dir,
            addon_loader=self._manager.addon_loader,
            main_entry=self._manager.addon_entries.main,
            register_plugin=self._register_plugin,
        )
        result = adapter.execute(
            plugin_id,
            entry_kind=entry_kind,
            entry_path=entry_path,
            project_work_path=project_work_path,
            project_output_path=project_output_path,
            tool_bin=tool_bin,
            tool_version=tool_version,
            language=language,
            temp_path=temp_path,
            module_exec=module_exec,
            values=values,
        )
        if (
            result == 0
            and plugin_id
            and not self.is_installed(plugin_id)
            and not self.is_virtual(plugin_id)
        ):
            self.request_plugin_list_refresh()
        return result

    def install(self, package_path: str):
        with operation_context("plugin.install", package_path=package_path):
            logger.info("plugin.install.started: package_path=%s", package_path)
            result = self._manager.install(package_path)
            logger.info(
                "plugin.install.completed: package_path=%s result=%r",
                package_path,
                result,
            )
            return result

    def uninstall(self, plugin_id: str, *, include_dependents: bool = True):
        with operation_context(
            "plugin.uninstall",
            plugin_id=plugin_id,
            include_dependents=include_dependents,
        ):
            logger.info(
                "plugin.uninstall.started: plugin_id=%s include_dependents=%s",
                plugin_id,
                include_dependents,
            )
            result = self._manager.uninstall_plugin(
                plugin_id,
                include_dependents=include_dependents,
            )
            logger.info(
                "plugin.uninstall.completed: plugin_id=%s result=%r",
                plugin_id,
                result,
            )
            return result

    def export(
        self,
        plugin_id: str,
        *,
        output_dir: str,
        output: object | None = None,
    ):
        with operation_context(
            "plugin.export",
            plugin_id=plugin_id,
            output_dir=output_dir,
        ):
            logger.info(
                "plugin.export.started: plugin_id=%s output_dir=%s",
                plugin_id,
                output_dir,
            )
            result = self._manager.export(
                plugin_id,
                output_dir=output_dir,
                output=output,
            )
            logger.info(
                "plugin.export.completed: plugin_id=%s result=%r",
                plugin_id,
                result,
            )
            return result

    def check_package(self, path: str):
        logger.debug("plugin.package_check: path=%s", path)
        return self._manager.check_mpk(path)

    def create_scaffold(self, data: Mapping[str, object]) -> str:
        with operation_context("plugin.scaffold", plugin_id=data.get("id")):
            result = str(self._manager.create_plugin_scaffold(dict(data)))
            logger.info("plugin.scaffold.completed: result=%s", result)
            return result

    def plugin_config_path(self, plugin_id: str) -> str | None:
        return self._manager.plugin_config_path(plugin_id)

    def is_installed(self, plugin_id: str) -> bool:
        return bool(self._manager.is_installed(plugin_id))

    def is_virtual(self, plugin_id: str) -> bool:
        return bool(self._manager.is_virtual(plugin_id))

    def get_name(self, plugin_id: str) -> str:
        return str(self._manager.get_name(plugin_id))

    def collect_dependent_plugin_ids(self, plugin_id: str) -> list[str]:
        return list(self._manager.collect_dependent_plugin_ids(plugin_id))


__all__ = ["PluginGateway"]
