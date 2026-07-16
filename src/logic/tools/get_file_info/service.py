from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable

from src.core.file_types import gettype


@dataclass(frozen=True)
class FileInfo:
    name: str
    path: str
    file_type: str
    size_bytes: int
    created_time: str


def normalize_input_path(file_list: list[object]) -> str:
    if not file_list:
        return ''
    value = file_list[0]
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value.decode('gbk')
    return str(value)


def describe_file(
    path: str,
    *,
    gettype_func: Callable[[str], str] = gettype,
    is_file: Callable[[str], bool] = os.path.isfile,
    get_size: Callable[[str], int] = os.path.getsize,
    get_ctime: Callable[[str], float] = os.path.getctime,
) -> FileInfo | None:
    normalized = str(path or '').strip()
    if not normalized or not is_file(normalized):
        return None
    size = get_size(normalized)
    return FileInfo(
        name=os.path.basename(normalized),
        path=normalized,
        file_type=gettype_func(normalized),
        size_bytes=size,
        created_time=time.ctime(get_ctime(normalized)),
    )


__all__ = ['FileInfo', 'describe_file', 'normalize_input_path']
