from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PluginEditorTarget:
    directory: Path
    filename: str
    python_source: bool


class PluginEditorService:
    def __init__(self, *, module_dir: str | Path):
        self.module_dir = Path(module_dir).resolve()

    def prepare_target(self, plugin_id: str, *, is_virtual: bool) -> PluginEditorTarget:
        if not plugin_id:
            raise ValueError('Plugin ID is empty')
        if is_virtual:
            raise ValueError(f'Virtual plugin cannot be edited: {plugin_id}')
        plugin_dir = (self.module_dir / plugin_id).resolve()
        try:
            plugin_dir.relative_to(self.module_dir)
        except ValueError as exc:
            raise ValueError(f'Plugin ID escapes the module directory: {plugin_id}') from exc
        if plugin_dir == self.module_dir or not plugin_dir.is_dir():
            raise FileNotFoundError(plugin_dir)
        python_entrypoint = plugin_dir / 'main.py'
        if python_entrypoint.is_file():
            return PluginEditorTarget(plugin_dir, 'main.py', True)
        shell_entrypoint = plugin_dir / 'main.sh'
        if not shell_entrypoint.exists():
            with shell_entrypoint.open('w', encoding='utf-8', newline='\n') as stream:
                stream.write("echo 'MIO-KITCHEN'\n")
        return PluginEditorTarget(plugin_dir, 'main.sh', False)


__all__ = ['PluginEditorService', 'PluginEditorTarget']
