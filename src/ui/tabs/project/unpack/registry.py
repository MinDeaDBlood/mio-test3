from __future__ import annotations

from collections import OrderedDict
from importlib import import_module

_MODULE_NAMES = [
    'src.ui.tabs.project.unpack.br.view',
    'src.ui.tabs.project.unpack.dat.view',
    'src.ui.tabs.project.unpack.dat_xz.view',
    'src.ui.tabs.project.unpack.img.view',
    'src.ui.tabs.project.unpack.sparse.view',
    'src.ui.tabs.project.unpack.payload.view',
    'src.ui.tabs.project.unpack.super.view',
    'src.ui.tabs.project.unpack.update_app.view',
    'src.ui.tabs.project.unpack.zst.view',
]

_SPECS = None


def _load_specs():
    global _SPECS
    if _SPECS is None:
        modules = [import_module(name) for name in _MODULE_NAMES]
        _SPECS = OrderedDict((module.SPEC.option_value, module.SPEC) for module in modules)
    return _SPECS


def get_specs():
    return tuple(_load_specs().values())


def get_option_values():
    return tuple(_load_specs().keys())


def has_option(value: str) -> bool:
    return value in _load_specs()


def get_spec(value: str):
    return _load_specs()[value]
