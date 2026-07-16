from src.core.diagnostics import emit
#!/usr/bin/env python3

# source from https://github.com/ilyakurdyukov/spreadtrum_flash/blob/main/unpac/unpac.c
# rewritten to python by affggh
import ctypes
from io import SEEK_SET
from os import makedirs
from os.path import exists
from os.path import join as path_join
from enum import Enum


class CommonStruct(ctypes.LittleEndianStructure):
    @property
    def _size(self):
        return ctypes.sizeof(type(self))

    def __len__(self):
        return self._size

    def unpack(self, data: bytes):
        if len(data) < self._size:
            raise Exception("Input data size less than struct size.")
        if not isinstance(data, (bytes, bytearray)):
            raise Exception("Input data must be byte data or bytearray.")

        return ctypes.memmove(ctypes.byref(self), data, self._size)

    def pack(self) -> bytes:
        return bytes(self)


class SprdHead(CommonStruct):
    _fields_ = [
        ("pac_version", ctypes.c_uint16 * 24),
        ("pac_size", ctypes.c_uint32),
        ("fw_name", ctypes.c_uint16 * 256),
        ("fw_version", ctypes.c_uint16 * 256),
        ("file_count", ctypes.c_uint32),
        ("dir_offset", ctypes.c_uint32),
        ("unknow1", ctypes.c_uint32 * 5),
        ("fw_alias", ctypes.c_uint16 * 100),
        ("unknow2", ctypes.c_uint32 * 3),
        ("unknow", ctypes.c_uint32 * 200),
        ("pac_magic", ctypes.c_uint32),
        ("head_crc", ctypes.c_uint16),
        ("data_crc", ctypes.c_uint16),
    ]


class SprdFile(CommonStruct):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("id", ctypes.c_uint16 * 256),
        ("name", ctypes.c_uint16 * 256),
        ("unknow1", ctypes.c_uint16 * 256),
        ("size", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("flash_use", ctypes.c_uint32),
        ("pac_offset", ctypes.c_uint32),
        ("omit_flag", ctypes.c_uint32),
        ("addr_num", ctypes.c_uint32),
        ("addr", ctypes.c_uint32 * 5),
        ("unknow2", ctypes.c_uint32 * 249),
    ]


def convert_u16_to_string(data):
    byte_data: bytes = bytes(data)
    return byte_data.decode("utf-16")


class FileTypes(Enum):
    operation = 0
    file = 1
    xml = 2
    fdl = 0x101


class MODE(Enum):
    NONE = 0
    LIST = 1
    EXTRACT = 2
    CHECK = 3


def crc16(crc: int, src: bytes):
    for byte in src:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if (crc & 1) else 0)
    return crc


def check_path(path):
    invalid_str = ["/", "\\", ":"]
    for s in invalid_str:
        if s in path:
            return False
    return True


def unpac(image_path: str, out_dir: str, mode: MODE = MODE.LIST):
    if not exists(out_dir):
        makedirs(out_dir, exist_ok=True)
    chunk = 0x1000
    head = SprdHead()
    # file = sprd_file()

    with open(image_path, "rb") as fi:
        head.unpack(fi.read(len(head)))

        if head.pac_magic != 0xFFFAFFFA:  # ~0x50005u
            raise Exception("Bad pac_magic!")

        if mode == MODE.LIST:
            emit("pac_version: %s" % convert_u16_to_string(head.pac_version))
            emit("pac_size: %u" % head.pac_size)

            emit("fw_name: %s" % convert_u16_to_string(head.fw_version))
            emit("fw_version: %s" % convert_u16_to_string(head.fw_version))
            emit("fw_alias: %s" % convert_u16_to_string(head.fw_alias))

        if mode == MODE.LIST or mode == MODE.CHECK:
            head_crc = crc16(0, head.pack()[: len(head) - 4])
            emit("head_crc: 0x%04x" % head.head_crc)
            if head.head_crc != head_crc:
                emit("(expected 0x%04x)" % head_crc)

        if head.dir_offset != len(head):
            raise Exception("unexpected directory offset")

        if (head.file_count >> 10) != 0:
            raise Exception("too many files")

        if mode == MODE.LIST or mode == MODE.EXTRACT:
            for i in range(head.file_count):
                file = SprdFile()
                file.unpack(fi.read(len(file)))

                if file.struct_size != len(file):
                    raise Exception("unexpected struct size")

                if mode == MODE.EXTRACT:
                    if (
                        (file.name[0] == 0)
                        or (file.pac_offset == 0)
                        or (file.size == 0)
                    ):
                        continue

                if mode == MODE.LIST:
                    emit(f"type = {FileTypes(file.type).name}", end="")
                    if file.size > 0:
                        emit(", size = 0x%x" % file.size, end="")
                    if file.pac_offset > 0:
                        emit(", offset = 0x%x" % file.pac_offset, end="")

                    if file.addr_num <= 5:
                        for j in range(file.addr_num):
                            if file.addr[j] == 0:
                                continue
                            if j <= 0:
                                emit(", addr = 0x%x" % file.addr[j], end="")
                            else:
                                emit(", addr%u = 0x%x" % (j, file.addr[j]), end="")

                    if file.id[0] != 0:
                        emit(', id = "%s"' % convert_u16_to_string(file.id), end="")

                    if file.name[0] != 0:
                        emit(', name = "%s"' % convert_u16_to_string(file.name), end="")

                    emit()
                else:
                    file_name = convert_u16_to_string(file.name).strip("\0")
                    emit(file_name)

                    fi.seek(file.pac_offset, SEEK_SET)
                    if not check_path(file_name):
                        emit("!!! unsafe filename detected!")
                        continue

                    with open(path_join(out_dir, file_name), "wb") as fo:
                        file_size = file.size
                        for n in range(0, file_size, chunk):
                            buf = fi.read(
                                chunk if file_size - n > chunk else file_size - n
                            )
                            fo.write(buf)

                    fi.seek(len(head) + (i + 1) * len(file), SEEK_SET)

        elif mode == MODE.CHECK:
            pac_size = head.pac_size
            data_crc = 0
            n = head._size

            if pac_size < n:
                raise Exception("unexpected pac size")
            for n in range(0, pac_size, chunk):
                buf = fi.read(chunk if pac_size - n > chunk else pac_size - n)
                data_crc = crc16(data_crc, buf)

            emit("data_crc: 0x%04x" % head.data_crc)
            if head.data_crc != data_crc:
                emit("(ecpected 0x%04x)" % data_crc)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="unpac", usage="<list|extract|check> -d out pac_file"
    )
    parser.add_argument("command")
    parser.add_argument("-d,--dir", metavar="outdir", dest="outdir")
    parser.add_argument("pac_file")

    args = parser.parse_args()

    command = args.command
    outdir = "out"
    if args.outdir:
        outdir = args.outdir

    pac_file = args.pac_file

    mode = MODE.NONE

    if command == "list":
        mode = MODE.LIST
    elif command == "check":
        mode = MODE.CHECK
    elif command == "extract":
        mode = MODE.EXTRACT
    else:
        raise Exception("Unsupported command")

    if not exists(outdir):
        makedirs(outdir)

    unpac(pac_file, outdir, mode)
