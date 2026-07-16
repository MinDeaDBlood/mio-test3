"""Lazy public facade for import-flow helpers."""

from __future__ import annotations


def copy_project(*args, **kwargs):
    from .service import copy_project as _copy_project
    return _copy_project(*args, **kwargs)


def script2fs(*args, **kwargs):
    from .service import script2fs as _script2fs
    return _script2fs(*args, **kwargs)


def unpackrom(*args, **kwargs):
    from .service import unpackrom as _unpackrom
    return _unpackrom(*args, **kwargs)


__all__ = ['copy_project', 'script2fs', 'unpackrom']
