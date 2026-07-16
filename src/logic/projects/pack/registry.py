from __future__ import annotations

from collections import OrderedDict
from importlib import import_module

_MODULE_NAMES = ['src.logic.projects.pack.img.controller', 'src.logic.projects.pack.sparse.controller', 'src.logic.projects.pack.dat.controller', 'src.logic.projects.pack.br.controller']

_CONTROLLERS = None


def _load_controllers():
    global _CONTROLLERS
    if _CONTROLLERS is None:
        modules = [import_module(name) for name in _MODULE_NAMES]
        _CONTROLLERS = OrderedDict((module.get_output_format(), module) for module in modules)
    return _CONTROLLERS


def get_output_formats():
    return tuple(_load_controllers().keys())


def apply_output_format(format_name: str, work_output: str, partition_name: str, *, brotli_level: int = 0, dat_version: int = 4, output=None):
    return _load_controllers()[format_name].execute(work_output, partition_name, brotli_level=brotli_level, dat_version=dat_version, output=output)
