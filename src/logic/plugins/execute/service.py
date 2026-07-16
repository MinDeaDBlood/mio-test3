from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping

from src.core import imp
from src.logic.common.messages import message
from src.core.process_runner import call
from src.logic.plugins.runtime_context import PluginExecuteRuntimeContext
from src.logic.projects.common.fs_service import re_folder


class PluginExecuteService:
    def __init__(
        self,
        *,
        module_dir: str,
        addon_loader,
        addon_entries,
        is_virtual,
        get_name,
        register_plugin,
        runtime: PluginExecuteRuntimeContext,
        logger=None,
    ):
        self.module_dir = module_dir
        self.addon_loader = addon_loader
        self.addon_entries = addon_entries
        self.is_virtual = is_virtual
        self.get_name = get_name
        self.register_plugin = register_plugin
        self.runtime = runtime
        self.logger = logger or logging

    def run(self, plugin_id=None) -> int:
        if not plugin_id:
            return 0
        if not self.runtime.project_name:
            self.runtime.output.log(
                message("project_not_selected", "Project is not selected")
            )
            return 1
        script_path = os.path.join(self.module_dir, plugin_id)
        if not self.is_virtual(plugin_id):
            name = self.get_name(plugin_id)
            info_json_path = os.path.join(script_path, "info.json")
            if not os.path.exists(info_json_path):
                self.logger.error(
                    "run: info.json not found for plugin %s at %s",
                    plugin_id,
                    info_json_path,
                )
                self.runtime.output.log(f"Plugin {name} configuration is missing.")
                return 3
            try:
                with open(info_json_path, "r", encoding="UTF-8") as stream:
                    data = json.load(stream)
            except json.JSONDecodeError:
                self.logger.error(
                    "run: Could not decode info.json for plugin %s", plugin_id
                )
                self.runtime.output.log(f"Plugin {name} configuration is corrupted.")
                return 4
            except OSError as exc:
                self.logger.error(
                    "run: Error reading info.json for plugin %s: %s", plugin_id, exc
                )
                self.runtime.output.log(f"Error accessing plugin {name} configuration.")
                return 5
            for dependency in data.get("depend", "").split():
                if dependency and not os.path.exists(
                    os.path.join(self.module_dir, dependency)
                ):
                    self.runtime.output.log(
                        message(
                            "plugin_dependency_missing",
                            "Plugin {plugin} requires missing dependency {dependency}",
                            plugin=name,
                            dependency=dependency,
                        )
                    )
                    return 2

        values = self.runtime.values

        main_sh_path = os.path.join(script_path, "main.sh")
        main_py_path = os.path.join(script_path, "main.py")
        if os.path.exists(main_sh_path):
            return self._run_shell_plugin(script_path, main_sh_path, values)
        if os.path.exists(main_py_path) and imp:
            if not self.addon_loader.is_registered(plugin_id):
                self.register_plugin(plugin_id)
            self.addon_loader.run(
                plugin_id, self.addon_entries.main, mapped_args=dict(values)
            )
        elif self.is_virtual(plugin_id):
            self.addon_loader.run(
                plugin_id, self.addon_entries.main, mapped_args=dict(values)
            )
        elif not os.path.exists(script_path):
            self.runtime.output.report(
                message(
                    "plugin_not_found",
                    "Plugin not found: {plugin_id}",
                    plugin_id=plugin_id,
                )
            )
        else:
            self.runtime.output.log(
                message(
                    "plugin_entry_missing",
                    "Plugin entry point is missing: {plugin}",
                    plugin=self.get_name(plugin_id),
                )
            )
        return 0

    def _run_shell_plugin(
        self, script_path: str, main_sh_path: str, values: Mapping[str, object]
    ) -> int:
        if not os.path.exists(self.runtime.temp_path):
            re_folder(self.runtime.temp_path)
        exports = ""
        for variable_name, value in values.items():
            current_value = str(value)
            if current_value:
                escaped = current_value.replace("'", "'\\''")
                exports += f"export {variable_name}='{escaped}';"
        norm_tool_bin = os.path.normpath(self.runtime.tool_bin).replace(os.sep, "/")
        norm_script_path = os.path.normpath(script_path).replace(os.sep, "/")
        norm_module_dir = os.path.normpath(self.module_dir).replace(os.sep, "/")
        norm_project_output = os.path.normpath(
            self.runtime.project_output_path
        ).replace(os.sep, "/")
        norm_project_work = os.path.normpath(self.runtime.project_work_path).replace(
            os.sep, "/"
        )
        norm_module_exec = os.path.normpath(self.runtime.module_exec).replace(
            os.sep, "/"
        )
        norm_main_sh_path = os.path.normpath(main_sh_path).replace(os.sep, "/")
        exports += f"export tool_bin='{norm_tool_bin}';"
        exports += f"export version='{self.runtime.tool_version}';"
        exports += f"export language='{self.runtime.language}';"
        exports += f"export bin='{norm_script_path}';"
        exports += f"export moddir='{norm_module_dir}';"
        exports += f"export project_output='{norm_project_output}';"
        exports += f"export project='{norm_project_work}';"
        shell_command_prefix = "ash" if os.name == "posix" else "bash"
        return call(
            [
                "busybox",
                shell_command_prefix,
                "-c",
                f"{exports} exec {norm_module_exec} {norm_main_sh_path}",
            ]
        )


def run_plugin(module_manager, plugin_id: str, *, runtime: PluginExecuteRuntimeContext):
    return module_manager.run(plugin_id, runtime=runtime)


__all__ = ["PluginExecuteService", "run_plugin"]
