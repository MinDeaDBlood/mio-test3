from __future__ import annotations
from src.core.diagnostics import emit

import os
import struct


class GuoKeLogo:
    def __init__(self):
        self.offset = 8192
        self.header_size = 128

    def unpack(self, file: str, output_dir: str):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(file, 'rb') as f:
            with open(os.path.join(output_dir, 'header'), 'wb') as header:
                header.write(f.read(self.header_size))
            with open(os.path.join(output_dir, 'image.jpg'), 'wb') as image:
                f.seek(self.offset)
                image.write(f.read())
        emit("Unpack Done!")

    def pack(self, output_dir, file):
        if os.path.exists(file):
            os.remove(file)
        if not os.path.exists(os.path.join(output_dir, 'header')) or not os.path.exists(
                os.path.join(output_dir, 'image.jpg')):
            emit('Cannot Pack The logo!:sth losing.')
        with open(file, 'wb') as f:
            with open(os.path.join(output_dir, 'header'), 'rb') as header:
                f.write(header.read())
            with open(os.path.join(output_dir, 'image.jpg'), 'rb') as image:
                f.write((self.offset - self.header_size) * b'\x00')
                f.write(image.read())
        emit('Pack Done!')


class Dumpcfg:
    blksz = 4096
    headoff = 16384
    magic = b"LOGO!!!!"
    imgnum = 0
    imgblkoffs = []
    imgblkszs = []


class Bmphead:
    def __init__(self, buf: bytes = None):
        assert buf is not None, f"buf Should be bytes, not {type(buf)}"
        (
            self.magic,
            self.fsize,
            self.reserved,
            self.hsize,
            self.dib,
            self.width,
            self.height,
        ) = struct.unpack("<H6I", buf)


class XiaomiBlkstruct:
    def __init__(self, buf: bytes):
        self.img_offset, self.blksz = struct.unpack("2I", buf)


class LogoDumper:
    def __init__(self, img: str, out: str, dir__: str = "pic"):
        self.magic = None
        self.out = out
        self.img = img
        self.dir = dir__
        self.struct_str = "<8s"
        self.cfg = Dumpcfg()
        self.check_img(img)

    def check_img(self, img: str):
        """Check whether an image can be unpacked as a Xiaomi logo image.

        The logo block table is only valid after the LOGO!!!! magic.  Older
        code parsed that table before checking the magic, which could turn a
        plain large binary into an expensive 8-byte-at-a-time scan.
        """
        assert os.access(img, os.F_OK), f"{img} does not exist!"
        with open(img, 'rb') as f:
            f.seek(self.cfg.headoff, 0)
            header = f.read(struct.calcsize(self.struct_str))
            if len(header) != struct.calcsize(self.struct_str):
                raise AssertionError("File is too small to contain xiaomi logo magic!")
            self.magic = struct.unpack(self.struct_str, header)[0]
            assert self.magic == b"LOGO!!!!", "File does not match xiaomi logo magic!"
            while True:
                chunk = f.read(8)
                if len(chunk) < 8:
                    break
                m = XiaomiBlkstruct(chunk)
                if m.img_offset != 0:
                    self.cfg.imgblkszs.append(m.blksz << 0xc)
                    self.cfg.imgblkoffs.append(m.img_offset << 0xc)
                    self.cfg.imgnum += 1
                else:
                    break
        return True

    def unpack(self):
        with open(self.img, 'rb') as f:
            emit("Unpack:\n"
                  "BMP\tSize\tWidth\tHeight")
            for i in range(self.cfg.imgnum):
                f.seek(self.cfg.imgblkoffs[i], 0)
                bmp_h = Bmphead(f.read(26))
                f.seek(self.cfg.imgblkoffs[i], 0)
                emit(f"{i:d}\t{bmp_h.fsize:d}\t{bmp_h.width:d}\t{bmp_h.height:d}")
                with open(os.path.join(self.out, f"{i}.bmp"), 'wb') as o:
                    o.write(f.read(bmp_h.fsize))
            emit("\tDone!")

    def repack(self) -> None:
        with open(self.out, 'wb') as o:
            off = 0x5
            for i in range(self.cfg.imgnum):
                emit(f"Write BMP [{i:d}.bmp] at offset 0x{off << 0xc:X}")
                with open(os.path.join(self.dir, f"{i}.bmp"), 'rb') as b:
                    bmp_head = Bmphead(b.read(26))
                    b.seek(0, 0)
                    self.cfg.imgblkszs[i] = (bmp_head.fsize >> 0xc) + 1
                    self.cfg.imgblkoffs[i] = off
                    o.seek(off << 0xc)
                    o.write(b.read(bmp_head.fsize))
                    off += self.cfg.imgblkszs[i]
            o.seek(self.cfg.headoff)
            o.write(self.magic)
            for i in range(self.cfg.imgnum):
                o.write(struct.pack("<I", self.cfg.imgblkoffs[i]))
                o.write(struct.pack("<I", self.cfg.imgblkszs[i]))
            emit("\tDone!")


__all__ = ['GuoKeLogo', 'Dumpcfg', 'Bmphead', 'XiaomiBlkstruct', 'LogoDumper']
