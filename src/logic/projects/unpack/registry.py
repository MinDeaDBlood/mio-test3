from __future__ import annotations

from collections import OrderedDict
from importlib import import_module
from types import ModuleType
from typing import Any

_FORMAT_MODULES = OrderedDict(
    (
        ('new.dat.br', 'src.logic.projects.unpack.br.controller'),
        ('new.dat', 'src.logic.projects.unpack.dat.controller'),
        ('new.dat.xz', 'src.logic.projects.unpack.dat_xz.controller'),
        ('img', 'src.logic.projects.unpack.img.controller'),
        ('sparse', 'src.logic.projects.unpack.sparse.controller'),
        ('payload', 'src.logic.projects.unpack.payload.controller'),
        ('super', 'src.logic.projects.unpack.super.controller'),
        ('update.app', 'src.logic.projects.unpack.update_app.controller'),
        ('zst', 'src.logic.projects.unpack.zst.controller'),
    )
)


class UnknownUnpackFormatError(KeyError):
    """Raised when an unpack format is not registered."""


def _normalize_format_name(format_name: str) -> str:
    key = str(format_name or '').strip()
    if key not in _FORMAT_MODULES:
        raise UnknownUnpackFormatError(f'Unknown unpack format: {format_name!r}')
    return key


def _load_controller(format_name: str) -> ModuleType:
    key = _normalize_format_name(format_name)
    controller = import_module(_FORMAT_MODULES[key])
    resolved_key = controller.get_format_name()
    if resolved_key != key:
        raise RuntimeError(
            f'Unpack controller format mismatch: registered {key!r}, '
            f'controller returned {resolved_key!r}'
        )
    return controller


def get_available_formats() -> tuple[str, ...]:
    """Return registered unpack formats without importing heavy controllers."""

    return tuple(_FORMAT_MODULES.keys())


def list_candidates(format_name: str, work: str) -> list[Any]:
    return _load_controller(format_name).list_candidates(work)


def run_unpack(format_name: str, selected, unpack_func=None):
    return _load_controller(format_name).execute(selected, unpack_func=unpack_func)


__all__ = [
    'UnknownUnpackFormatError',
    'get_available_formats',
    'list_candidates',
    'run_unpack',
]
