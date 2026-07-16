from __future__ import annotations

import os

from src.logic.editor import service


class EditorController:
    def __init__(self, *, logger=None):
        self.logger = logger

    def ensure_directory(self, path: str):
        return service.ensure_directory(path)

    def list_entries(self, path: str):
        return service.list_entries(path)

    def read_file(self, path: str, encoding: str):
        return service.read_file(path, encoding)

    def write_file(self, path: str, text: str):
        return service.write_file(path, text)

    def delete_entry(self, path: str):
        return service.delete_entry(path)

    def rename_entry(self, path: str, new_path: str):
        return service.rename_entry(path, new_path)

    def create_empty_file(self, path: str):
        return service.create_empty_file(path)

    def build_new_path(self, base_path: str, name: str) -> str:
        return os.path.join(base_path, name)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)

    def is_file(self, path: str) -> bool:
        return os.path.isfile(path)
