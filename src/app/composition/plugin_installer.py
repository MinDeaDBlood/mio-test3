from __future__ import annotations

from src.app.localization_runtime import lang
from src.app.plugins.installer_controller import PluginInstallerController
from src.app.plugins.runtime import build_plugin_ui_runtime_context
from src.logic.plugins.package_reader import PluginPackageReader
from src.ui.tabs.plugins.installer.window import PluginInstallerWindow


def open_plugin_installer(path: str):
    if not path:
        raise ValueError('MPK path is required')
    runtime = build_plugin_ui_runtime_context()
    controller = PluginInstallerController(
        runtime=runtime,
        package_reader=PluginPackageReader(),
    )
    return PluginInstallerWindow(
        path,
        texts=lang,
        controller=controller,
        error_codes=runtime.module_error_codes,
    )


__all__ = ['open_plugin_installer']
