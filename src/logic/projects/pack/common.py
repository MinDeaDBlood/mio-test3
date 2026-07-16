from __future__ import annotations

from src.logic.projects.common.fs_service import re_folder
from src.logic.projects.dtbo.service import pack_dtbo as _pack_dtbo
from src.logic.projects.dtbo.service import unpack_dtbo as _unpack_dtbo
from src.logic.projects.logo.service import dump_logo as _dump_logo
from src.logic.projects.logo.service import pack_logo as _pack_logo


def un_dtbo(bn: str = 'dtbo') -> None:
    return _unpack_dtbo(bn)


def pack_dtbo() -> bool:
    return _pack_dtbo()


def logo_dump(file_path, output: str = None, output_name: str = 'logo'):
    return _dump_logo(file_path, output, output_name)


def logo_pack(origin_logo=None) -> int:
    return _pack_logo(origin_logo)


__all__ = ['logo_dump', 'logo_pack', 'pack_dtbo', 're_folder', 'un_dtbo']
