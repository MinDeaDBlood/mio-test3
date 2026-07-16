from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable
from shutil import rmtree

from src.logic.common.messages import message
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.plugins.uninstall.result import PluginUninstallResult


PluginListProvider = Callable[[], Iterable[str]]
PluginInfoProvider = Callable[[str, str, object], object]
PluginNameProvider = Callable[[str], str]
PluginPredicate = Callable[[str], bool]
PluginStateNotifier = Callable[[str], None]


class PluginUninstallService:
    """Own plugin removal and dependent cleanup rules."""

    def __init__(
        self,
        *,
        module_dir: str,
        list_packages: PluginListProvider,
        get_info: PluginInfoProvider,
        get_name: PluginNameProvider,
        is_virtual: PluginPredicate,
        notify_plugin_state_changed: PluginStateNotifier,
        logger: logging.Logger | None = None,
        output: ServiceOutput | None = None,
    ) -> None:
        self.module_dir = module_dir
        self.list_packages = list_packages
        self.get_info = get_info
        self.get_name = get_name
        self.is_virtual = is_virtual
        self.notify_plugin_state_changed = notify_plugin_state_changed
        self.logger = logger or logging.getLogger(__name__)
        self.output = output or build_service_output()

    def collect_dependent_plugin_ids(self, plugin_id: str) -> list[str]:
        collected: list[str] = []
        seen: set[str] = set()

        def walk(current_id: str) -> None:
            for installed_plugin_id in self.list_packages():
                if installed_plugin_id == current_id or installed_plugin_id in seen:
                    continue
                raw_dependencies = self.get_info(
                    installed_plugin_id,
                    'depend',
                    '',
                )
                if not isinstance(raw_dependencies, str):
                    self.logger.warning(
                        'Plugin dependency metadata for %s must be a string',
                        installed_plugin_id,
                    )
                    continue
                if current_id in raw_dependencies.split():
                    seen.add(installed_plugin_id)
                    collected.append(installed_plugin_id)
                    walk(installed_plugin_id)

        walk(plugin_id)
        return collected

    def _remove_plugin_dir(
        self,
        plugin_id: str,
        show_name: str = '',
    ) -> tuple[bool, str]:
        module_path = os.path.join(self.module_dir, plugin_id)
        display_name = show_name or plugin_id
        self.output.log(
            message(
                'plugin_uninstalling',
                'Uninstalling plugin: {plugin}',
                plugin=display_name,
            )
        )
        if not os.path.exists(module_path):
            self.logger.info(
                'Plugin directory %r is missing for %r and is treated as removed',
                module_path,
                plugin_id,
            )
            self.output.log(
                message(
                    'plugin_uninstalled',
                    'Plugin uninstalled: {plugin}',
                    plugin=display_name,
                )
            )
            return True, ''
        try:
            rmtree(module_path)
        except PermissionError as exc:
            self.logger.exception(
                'Permission error removing %r for %r: %s',
                module_path,
                plugin_id,
                exc,
            )
            return (
                False,
                f"Permission denied for '{module_path}'. Error: {exc}",
            )
        except OSError as exc:
            self.logger.exception(
                'File system error removing %r for %r: %s',
                module_path,
                plugin_id,
                exc,
            )
            return (
                False,
                f"Failed to remove '{module_path}'. Error: {exc}",
            )

        if os.path.exists(module_path):
            self.logger.warning(
                'Plugin directory %r still exists after removal',
                module_path,
            )
            return False, f'Failed to remove plugin {display_name}'

        self.logger.info('Removed plugin directory %r', module_path)
        self.output.log(
            message(
                'plugin_uninstalled',
                'Plugin uninstalled: {plugin}',
                plugin=display_name,
            )
        )
        return True, ''

    def uninstall_plugin(
        self,
        plugin_id: str,
        *,
        include_dependents: bool = True,
    ) -> PluginUninstallResult:
        if not plugin_id:
            return False, 'Please select a plugin.', []
        if self.is_virtual(plugin_id):
            return (
                False,
                f"Plugin '{self.get_name(plugin_id)}' is virtual and cannot be uninstalled this way.",
                [],
            )

        ordered_ids = (
            self.collect_dependent_plugin_ids(plugin_id)
            if include_dependents
            else []
        )
        ordered_ids.append(plugin_id)
        removed_ids: list[str] = []

        for current_id in ordered_ids:
            ok, error_message = self._remove_plugin_dir(
                current_id,
                self.get_name(current_id),
            )
            if not ok:
                return False, error_message, removed_ids
            removed_ids.append(current_id)
            self.notify_plugin_state_changed(current_id)

        return True, '', removed_ids


__all__ = [
    'PluginInfoProvider',
    'PluginListProvider',
    'PluginNameProvider',
    'PluginPredicate',
    'PluginStateNotifier',
    'PluginUninstallService',
]
