from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from src.core.process_runner import call
from src.platform.operation_logging import operation_context

logger = logging.getLogger(__name__)


class PluginExecutionAdapter:
    """Execute one already validated third party plugin plan."""

    def __init__(
        self,
        *,
        module_dir: str,
        addon_loader: Any,
        main_entry: object,
        register_plugin: Callable[[str], None],
    ) -> None:
        self.module_dir = module_dir
        self.addon_loader = addon_loader
        self.main_entry = main_entry
        self.register_plugin = register_plugin

    def execute(
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
        with operation_context(
            "plugin.runtime.execute",
            plugin_id=plugin_id,
            entry_kind=entry_kind,
            entry_path=entry_path,
        ):
            logger.info(
                "plugin.runtime.started: plugin_id=%s entry_kind=%s entry_path=%s "
                "work_path=%s output_path=%s argument_names=%s",
                plugin_id,
                entry_kind,
                entry_path,
                project_work_path,
                project_output_path,
                tuple(sorted(values)),
            )
            if entry_kind == "shell":
                result = self._run_shell_plugin(
                    plugin_id,
                    script_path=str(Path(entry_path).parent),
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
            elif entry_kind == "python":
                if not self.addon_loader.is_registered(plugin_id):
                    self.register_plugin(plugin_id)
                self._invoke_registered_plugin(plugin_id, values)
                result = 0
            elif entry_kind == "virtual":
                self._invoke_registered_plugin(plugin_id, values)
                result = 0
            else:
                raise ValueError(f"Unsupported plugin entry kind: {entry_kind}")
            logger.info(
                "plugin.runtime.completed: plugin_id=%s entry_kind=%s result=%s",
                plugin_id,
                entry_kind,
                result,
            )
            return result

    def _invoke_registered_plugin(
        self,
        plugin_id: str,
        values: Mapping[str, object],
    ) -> None:
        logger.info(
            "plugin.runtime.python_invoke: plugin_id=%s argument_names=%s",
            plugin_id,
            tuple(sorted(values)),
        )
        self.addon_loader.run(
            plugin_id,
            self.main_entry,
            mapped_args=dict(values),
        )

    def _run_shell_plugin(
        self,
        plugin_id: str,
        *,
        script_path: str,
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
        runtime_temp = Path(temp_path)
        if not runtime_temp.exists():
            logger.info(
                "plugin.runtime.temp_create: plugin_id=%s path=%s",
                plugin_id,
                runtime_temp,
            )
            runtime_temp.mkdir(parents=True, exist_ok=True)

        exports = ""
        for variable_name, value in values.items():
            current_value = str(value)
            if current_value:
                escaped = current_value.replace("'", "'\\''")
                exports += f"export {variable_name}='{escaped}';"

        def normalized(value: str) -> str:
            return os.path.normpath(value).replace(os.sep, "/")

        norm_entry_path = normalized(entry_path)
        exports += f"export tool_bin='{normalized(tool_bin)}';"
        exports += f"export version='{tool_version}';"
        exports += f"export language='{language}';"
        exports += f"export bin='{normalized(script_path)}';"
        exports += f"export moddir='{normalized(self.module_dir)}';"
        exports += f"export project_output='{normalized(project_output_path)}';"
        exports += f"export project='{normalized(project_work_path)}';"
        shell_command_prefix = "ash" if os.name == "posix" else "bash"
        command = [
            "busybox",
            shell_command_prefix,
            "-c",
            f"{exports} exec {normalized(module_exec)} {norm_entry_path}",
        ]
        logger.info(
            "plugin.runtime.shell_launch: plugin_id=%s shell=%s entry=%s "
            "work_path=%s output_path=%s argument_names=%s",
            plugin_id,
            shell_command_prefix,
            entry_path,
            project_work_path,
            project_output_path,
            tuple(sorted(values)),
        )
        result = int(
            call(
                command,
                log_command=[
                    "busybox",
                    shell_command_prefix,
                    "-c",
                    f"<plugin environment redacted> exec {normalized(module_exec)} {norm_entry_path}",
                ],
            )
        )
        logger.info(
            "plugin.runtime.shell_exit: plugin_id=%s return_code=%s",
            plugin_id,
            result,
        )
        return result


__all__ = ["PluginExecutionAdapter"]
