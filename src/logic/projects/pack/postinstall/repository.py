from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .models import PostInstallEntry

_ATTRIBUTES = (
    'RUN_POSTINSTALL',
    'POSTINSTALL_PATH',
    'FILESYSTEM_TYPE',
    'POSTINSTALL_OPTIONAL',
)


def validate_partition_name(partition: str) -> str:
    normalized = partition.strip()
    if not normalized or normalized != partition:
        raise ValueError('Partition name must not be empty or contain surrounding whitespace')
    if any(char in normalized for char in ('=', '\n', '\r')):
        raise ValueError('Partition name contains unsupported characters')
    return normalized


class PostInstallConfigRepository:
    def __init__(self, config_file: str | Path):
        self.config_file = Path(config_file)

    def load(self) -> dict[str, PostInstallEntry]:
        if not self.config_file.exists():
            return {}
        raw: dict[str, dict[str, str]] = {}
        for line_number, raw_line in enumerate(self.config_file.read_text(encoding='utf-8').splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                raise ValueError(f'Invalid postinstall line {line_number}: missing =')
            name, value = line.split('=', 1)
            attribute, partition = self._split_name(name, line_number)
            raw.setdefault(partition, {})[attribute] = value
        return {
            partition: PostInstallEntry(
                partition=partition,
                run_postinstall=values.get('RUN_POSTINSTALL', 'false').lower() == 'true',
                postinstall_path=values.get('POSTINSTALL_PATH', ''),
                filesystem_type=values.get('FILESYSTEM_TYPE', ''),
                postinstall_optional=values.get('POSTINSTALL_OPTIONAL', 'false').lower() == 'true',
            )
            for partition, values in raw.items()
        }

    def save(self, entries: Iterable[PostInstallEntry]) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for entry in entries:
            partition = validate_partition_name(entry.partition)
            values = {
                'RUN_POSTINSTALL': str(entry.run_postinstall).lower(),
                'POSTINSTALL_PATH': entry.postinstall_path,
                'FILESYSTEM_TYPE': entry.filesystem_type,
                'POSTINSTALL_OPTIONAL': str(entry.postinstall_optional).lower(),
            }
            for name in _ATTRIBUTES:
                value = values[name]
                if value != '':
                    lines.append(f'{name}_{partition}={value}\n')
        with self.config_file.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(''.join(lines))

    @staticmethod
    def _split_name(name: str, line_number: int) -> tuple[str, str]:
        for attribute in _ATTRIBUTES:
            prefix = f'{attribute}_'
            if name.startswith(prefix):
                partition = validate_partition_name(name[len(prefix):])
                return attribute, partition
        raise ValueError(f'Invalid postinstall line {line_number}: unknown attribute {name!r}')


__all__ = ['PostInstallConfigRepository', 'validate_partition_name']
