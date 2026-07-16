from __future__ import annotations

from src.app.runtime.models import BootstrapProjectPathRuntime, RuntimeBootstrapServices


def build_runtime_bootstrap_services() -> RuntimeBootstrapServices:
    """Construct the mandatory startup services explicitly."""
    from src.platform.runtime_paths import PLUGIN_INSTALL_DIR
    from src.platform.settings_repository import SettingsRepository
    from src.logic.plugins.models import ModuleErrorCodes
    from src.logic.plugins.module_manager import ModuleManager
    from src.logic.projects.common.project_manager import ProjectManager
    from src.core.paths import prog_path

    settings = SettingsRepository(load=False)
    settings.path = prog_path
    project_runtime = BootstrapProjectPathRuntime(workspace_path=settings.path)
    return RuntimeBootstrapServices(
        settings=settings,
        module_error_codes=ModuleErrorCodes,
        module_manager=ModuleManager(module_dir=PLUGIN_INSTALL_DIR),
        project_manager=ProjectManager(runtime=project_runtime),
    )


__all__ = [
    "BootstrapProjectPathRuntime",
    "RuntimeBootstrapServices",
    "build_runtime_bootstrap_services",
]
