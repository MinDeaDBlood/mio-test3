from __future__ import annotations

from src.logic.plugins.package_reader import PluginPackageReader


class PluginInstallerController:
    """Application controller for reading and installing MPK packages."""

    def __init__(self, *, runtime, package_reader: PluginPackageReader):
        self.runtime = runtime
        self.package_reader = package_reader
        self.module_manager = runtime.module_manager

    def read_package(self, path: str):
        return self.package_reader.read(path)

    def install(self, path: str, *, on_success, on_error) -> None:
        self.runtime.task_runner.run(
            self.module_manager.install,
            path,
            on_success=on_success,
            on_error=on_error,
        )

    def notify_catalog_changed(self) -> None:
        self.module_manager.request_plugin_list_refresh()


__all__ = ['PluginInstallerController']
