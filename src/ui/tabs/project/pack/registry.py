from __future__ import annotations

from collections import OrderedDict
from importlib import import_module

_MODULE_NAMES = ['src.ui.tabs.project.pack.img.view', 'src.ui.tabs.project.pack.sparse.view', 'src.ui.tabs.project.pack.dat.view', 'src.ui.tabs.project.pack.br.view']

_SPECS = None


def _load_specs():
    global _SPECS
    if _SPECS is None:
        modules = [import_module(name) for name in _MODULE_NAMES]
        _SPECS = OrderedDict((module.SPEC.output_value, module.SPEC) for module in modules)
    return _SPECS


def get_specs():
    return tuple(_load_specs().values())


def get_output_values():
    return tuple(_load_specs().keys())
