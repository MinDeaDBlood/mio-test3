from __future__ import annotations

from src.logic.tools.get_file_info.service import FileInfo, describe_file, normalize_input_path


class GetFileInfoController:
    """Application adapter for the file information use case."""

    def __init__(self, *, gettype_func) -> None:
        self._gettype_func = gettype_func

    @staticmethod
    def normalize_file(file_list: list[object]) -> str:
        return normalize_input_path(file_list)

    def read_info(self, path: str) -> FileInfo | None:
        return describe_file(path, gettype_func=self._gettype_func)


__all__ = ['GetFileInfoController']
