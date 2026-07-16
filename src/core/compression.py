from __future__ import annotations
from src.core.diagnostics import emit

import os
import traceback
from lzma import LZMADecompressor
from os.path import exists


class Unxz:
    def __init__(self, file_path: str, remove_src: bool = True, buff_size: int = 8192):
        self.remove_src = remove_src
        self.buff_size = buff_size
        self.file_path = file_path

        if not self.file_path.endswith('.xz'):
            emit('To use Unxz, File name must end with .xz, Stop.')
            return

        self.out_file = file_path.rsplit('.xz', 1)[0]
        if exists(self.out_file):
            emit(f'Output file {self.out_file!r} already exist! Not overwriting.')
            return

        try:
            self.do_unxz()
        except Exception:
            traceback.print_exc()
            try:
                os.remove(self.out_file)
            except OSError:
                ...
        else:
            if self.remove_src:
                try:
                    os.remove(self.file_path)
                except OSError:
                    ...

    def do_unxz(self):
        dec = LZMADecompressor()
        with open(self.file_path, 'rb') as in_fd, open(self.out_file, 'wb') as out_fd:
            while raw := in_fd.read(self.buff_size):
                while True:
                    raw = dec.decompress(raw, max_length=self.buff_size)
                    out_fd.write(raw)
                    if dec.needs_input or dec.eof:
                        break
                    raw = b''


__all__ = ['Unxz']
