from __future__ import annotations
from src.core.diagnostics import emit

import os


class Vbpatch:
    def __init__(self, file_):
        self.file = file_
        self.disavb = lambda: self.patchvb(b'\x02')

    def checkmagic(self) -> bool:
        """Check whether file has vbmeta magic."""
        if os.access(self.file, os.F_OK):
            with open(self.file, "rb") as f:
                return b'AVB0' == f.read(4)
        else:
            emit("File does not exist!")
        return False

    def patchvb(self, flag):
        if not self.checkmagic():
            return False
        if os.access(self.file, os.F_OK):
            with open(self.file, 'rb+') as f:
                f.seek(123, 0)
                f.write(flag)
            emit("Done!")
        else:
            emit("File not Found")
            return False
        return True


__all__ = ['Vbpatch']
