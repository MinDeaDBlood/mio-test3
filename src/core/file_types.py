from __future__ import annotations

import os
import struct
import tarfile

from src.core.logo import LogoDumper

# [header, desc, offset (if exist)]
formats = ([b'PK', "zip"], [b'OPPOENCRYPT!', "ozip"], [b'7z', "7z"], [b'\x53\xef', 'ext', 1080],
           [b'\x3a\xff\x26\xed', "sparse"], [b'\xe2\xe1\xf5\xe0', "erofs", 1024], [b"CrAU", "payload"],
           [b"AVB0", "vbmeta"], [b'EFI PART', 'gpt', 512], [b'SPLASH!!', 'splash', 1024], [b'\xd7\xb7\xab\x1e', "dtbo"], [b'\x10\x20\xF5\xF2', 'f2fs', 1024],
           [b'\xd0\x0d\xfe\xed', "dtb"], [b"MZ", "exe"], [b".ELF", 'elf'],
           [b'\x7fELF', 'elf'],
           [b"ANDROID!", "boot"], [b"VNDRBOOT", "vendor_boot"],
           [b'AVBf', "avb_foot"], [b'BZh', "bzip2"],
           [b'CHROMEOS', 'chrome'], [b'\x1f\x8b', "gzip"],
           [b'\x1f\x9e', "gzip"], [b'\x02\x21\x4c\x18', "lz4_legacy"],
           [b'\x03\x21\x4c\x18', 'lz4'], [b'\x04\x22\x4d\x18', 'lz4'],
           [b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\x03', "zopfli"], [b'\xfd7zXZ', 'lzma'],
           [b'\x5d\x00', 'lzma'],
           [b']\x00\x00\x00\x04\xff\xff\xff\xff\xff\xff\xff\xff', 'lzma'], [b'\x02!L\x18', 'lz4_lg'],
           [b'\x89PNG', 'png'], [b"LOGO!!!!", 'logo', 4000], [b'\x28\xb5\x2f\xfd', 'zstd'], [b"RSCE", 'rk_rsce'],
           [b'(\x05\x00\x00$8"%', 'kdz'], [b"\x32\x96\x18\x74", 'dz'], [b'\xcf\xfa\xed\xfe', 'macos_bin'],
           [b'\xfa\xff\xfa\xff', 'pac', 2116], [b"NTPI", 'NTPI'], [b'\x56\x19\xb5\x27', 'amlogic', 8],
           [b"-rom1fs-", 'romfs'], [b'UBI#', "ubi"], [b"sqsh", "squashfs"], [b'hsqs', 'squashfs'], [b"\x85\x19", "jffs2"], [b'RKFW', 'rkfw'], [b'RKAF', 'rkaf'],
           [b'###\x00|\x00\x00\x00LOGO_TABLE\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00P', 'guoke_logo']
           )


def zero_start(file: str, c: int, buff_size: int = 8192) -> bool:
    with open(file, 'rb') as f:
        zeros_ = bytearray(buff_size)
        while c:
            buf = f.read(min(c, buff_size))
            n = len(buf)
            if n != len(zeros_):
                zeros_ = bytearray(n)
            if buf != zeros_:
                return False
            c -= n
    return True


def is_empty_img(file):
    return zero_start(file, os.path.getsize(file))


def gettype(file) -> str:
    """Return the detected file type for a path."""
    if not os.path.isfile(file):
        return 'fnf'
    if not os.path.exists(file):
        return "fne"

    def is_super(fil) -> bool:
        with open(fil, 'rb') as file_:
            try:
                file_.seek(4096, 0)
                return file_.read(4) == b'\x67\x44\x6c\x61'
            except EOFError:
                return False

    try:
        if is_super(file):
            return 'super'
    except IndexError:
        ...
    for header, desc, *offset in formats:
        with open(file, 'rb') as f:
            f.seek(offset[0] if offset else 0)
            if f.read(len(header)) == header:
                return desc

    if not zero_start(file, 512) and tarfile.is_tarfile(file):
        return 'tar'
    try:
        if LogoDumper(file, str(None)).check_img(file):
            return 'logo'
    except AssertionError:
        ...
    except struct.error:
        ...
    return "unknown"


__all__ = ['formats', 'zero_start', 'is_empty_img', 'gettype']
