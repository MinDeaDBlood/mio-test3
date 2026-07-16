from __future__ import annotations
from src.core.diagnostics import emit

import hashlib
import os


def hashlib_calculate(file_path, method: str) -> int | str:
    if not hasattr(hashlib, method):
        emit(f"Warn, The algorithm {method} not exist in hashlib!")
        return 1
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        emit(f"Warn, The file {file_path} not exist!")
        return 1
    algorithm = getattr(hashlib, method)()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            algorithm.update(chunk)
    return algorithm.hexdigest()


def calculate_sha256_file(file_path):
    return hashlib_calculate(file_path, 'sha256')


def calculate_md5_file(file_path):
    return hashlib_calculate(file_path, 'md5')


__all__ = ['hashlib_calculate', 'calculate_sha256_file', 'calculate_md5_file']
