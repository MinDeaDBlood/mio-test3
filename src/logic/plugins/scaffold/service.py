from __future__ import annotations

import json
import os


class PluginScaffoldService:
    """Creates new plugin scaffolds without any UI dependencies."""

    def __init__(self, *, module_dir: str, notify_plugin_state_changed=None):
        self.module_dir = module_dir
        self.notify_plugin_state_changed = notify_plugin_state_changed

    def create_plugin_scaffold(self, data: dict) -> str:
        identifier = data.get('identifier')
        if not identifier:
            raise ValueError('Plugin identifier is required')
        plugin_dir = os.path.join(self.module_dir, identifier)
        os.makedirs(plugin_dir, exist_ok=True)
        with open(os.path.join(plugin_dir, 'info.json'), 'w+', encoding='utf-8', newline='\n') as js:
            json.dump(data, js, ensure_ascii=False, indent=4)
        if callable(self.notify_plugin_state_changed):
            self.notify_plugin_state_changed(identifier)
        return identifier
