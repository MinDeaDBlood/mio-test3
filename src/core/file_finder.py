from __future__ import annotations

import os
from os.path import exists


def get_all_file_paths(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            yield os.path.join(root, filename)


def remove_duplicate(file_) -> None:
    """Remove duplicate lines from a file while preserving first occurrence order."""
    if not exists(file_):
        return
    with open(file_, 'r+', encoding='utf-8', newline='\n') as f:
        data = f.readlines()
        data = sorted(set(data), key=data.index)
        f.seek(0)
        f.truncate()
        f.writelines(data)


def findfile(file, dir_) -> str:
    for root, _, files in os.walk(dir_, topdown=True):
        if file in files:
            if os.name == 'nt':
                return f'{root}/{file}'.replace("\\", '/')
            return f'{root}/{file}'
    return ''


def findfolder(dir__, folder_name):
    for root, dirnames, _ in os.walk(dir__):
        for dirname in dirnames:
            if dirname == folder_name:
                return os.path.join(root, dirname).replace("\\", '/')
    return None


__all__ = ['get_all_file_paths', 'remove_duplicate', 'findfile', 'findfolder']
