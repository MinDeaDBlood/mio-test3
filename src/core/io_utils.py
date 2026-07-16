from __future__ import annotations


class DevNull:
    def __init__(self):
        self.data = ''

    def write(self, string):
        self.data += string

    def flush(self):
        ...


__all__ = ['DevNull']
