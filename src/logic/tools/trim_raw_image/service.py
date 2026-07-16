from __future__ import annotations

import os
from typing import Callable


from src.logic.tools.trim_raw_image.models import TrimRawImageResult, TrimRawValidationError


def normalize_path(path: str) -> str:
    return str(path or '').strip()


def validate_path(path: str, *, is_file=os.path.isfile) -> TrimRawValidationError | None:
    normalized = normalize_path(path)
    if not normalized:
        return TrimRawValidationError.PATH_REQUIRED
    if not is_file(normalized):
        return TrimRawValidationError.FILE_NOT_FOUND
    return None


def trim_trailing_zeros(path: str, buff_size: int = 8192, progress_callback: Callable[[int], None] | None = None) -> int:
    orig_size = file_size = os.path.getsize(path)
    zeros_ = bytearray(buff_size)
    with open(path, 'rb') as handle:
        update_ui = 3000
        while file_size:
            n = min(file_size, buff_size)
            file_size_ = file_size - n
            handle.seek(file_size_)
            buf = handle.read(n)
            if n != len(zeros_):
                zeros_ = bytearray(n)
            if buf != zeros_:
                for i, byte in enumerate(reversed(buf)):
                    if byte != 0:
                        break
                file_size -= i
                break
            file_size = file_size_
            update_ui -= 1
            if update_ui == 0:
                update_ui = 3000
                if progress_callback and orig_size:
                    percentage = 100 - file_size * 100 // orig_size
                    progress_callback(int(percentage))
    os.truncate(path, file_size)
    return orig_size - file_size


def execute_trim(path: str, *, progress_callback: Callable[[int], None] | None = None) -> TrimRawImageResult:
    normalized = normalize_path(path)
    return TrimRawImageResult(trimmed_bytes=trim_trailing_zeros(normalized, progress_callback=progress_callback))


__all__ = [
    'TrimRawImageResult',
    'TrimRawValidationError',
    'execute_trim',
    'normalize_path',
    'trim_trailing_zeros',
    'validate_path',
]
