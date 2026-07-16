from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

from src.core.file_types import gettype


@dataclass(frozen=True)
class EditorReadResult:
    path: str
    file_type: str
    content: str | None
    error: Exception | None

    @property
    def succeeded(self) -> bool:
        return self.error is None


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def list_entries(path: str) -> list[str]:
    return ['..', *os.listdir(path)]


def read_file(path: str, encoding: str) -> EditorReadResult:
    try:
        with open(path, 'rb') as stream:
            raw_data = stream.read()
    except OSError as exc:
        return EditorReadResult(path=path, file_type=gettype(path), content=None, error=exc)
    try:
        content = raw_data.decode(encoding)
    except (UnicodeError, LookupError) as exc:
        return EditorReadResult(path=path, file_type=gettype(path), content=None, error=exc)
    return EditorReadResult(path=path, file_type=gettype(path), content=content, error=None)


def write_file(path: str, text: str) -> None:
    with open(path, 'w+', encoding='utf-8', newline='\n') as stream:
        stream.write(text)


def delete_entry(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


def rename_entry(path: str, new_path: str) -> None:
    os.rename(path, new_path)


def create_empty_file(path: str) -> None:
    ensure_directory(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8'):
        pass


__all__ = [
    'EditorReadResult',
    'create_empty_file',
    'delete_entry',
    'ensure_directory',
    'list_entries',
    'read_file',
    'rename_entry',
    'write_file',
]
