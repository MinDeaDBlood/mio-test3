def is_plugin_installed(module_manager, plugin_id: str) -> bool:
    return module_manager.is_installed(plugin_id)
