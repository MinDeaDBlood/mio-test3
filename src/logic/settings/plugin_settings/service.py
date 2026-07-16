def get_plugin_setting(module_manager, plugin_id: str, key: str, default=None):
    info = module_manager.get_info(plugin_id, key, default)
    return info
