from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

from src.core.config_parser import ConfigParser


class PluginPackageError(ValueError):
    pass


@dataclass(frozen=True)
class PluginPackageInfo:
    path: Path
    name: str
    version: str
    author: str
    description: str
    icon_data: bytes | None


class PluginPackageReader:
    def read(self, package_path: str | Path) -> PluginPackageInfo:
        path = Path(package_path).resolve()
        if not path.is_file():
            raise PluginPackageError(f'Plugin package does not exist: {path}')
        if not zipfile.is_zipfile(path):
            raise PluginPackageError(f'Plugin package is not a valid ZIP archive: {path}')
        try:
            with zipfile.ZipFile(path, 'r') as archive:
                names = set(archive.namelist())
                if 'info' not in names:
                    raise PluginPackageError('Plugin package has no info file')
                parser = ConfigParser()
                try:
                    parser.read_string(archive.read('info').decode('utf-8'))
                except UnicodeDecodeError as exc:
                    raise PluginPackageError('Plugin info file is not valid UTF-8') from exc
                module_section = parser.sections.get('module')
                if not isinstance(module_section, dict):
                    raise PluginPackageError('Plugin info has no module section')
                required = {
                    key: str(module_section.get(key, '')).strip()
                    for key in ('name', 'version', 'author', 'describe')
                }
                missing = [key for key, value in required.items() if not value]
                if missing:
                    raise PluginPackageError(f'Plugin info is missing fields: {", ".join(missing)}')
                icon_data = archive.read('icon') if 'icon' in names else None
        except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
            if isinstance(exc, PluginPackageError):
                raise
            raise PluginPackageError(f'Unable to read plugin package: {path}') from exc
        return PluginPackageInfo(
            path=path,
            name=required['name'],
            version=required['version'],
            author=required['author'],
            description=required['describe'],
            icon_data=icon_data,
        )


__all__ = ['PluginPackageError', 'PluginPackageInfo', 'PluginPackageReader']
