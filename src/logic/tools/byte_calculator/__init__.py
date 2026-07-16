from __future__ import annotations

from importlib import import_module

__all__ = ['convert', 'convert_text', 'format_number', 'parse_number']

_EXPORTS = {'convert': ('src.logic.tools.byte_calculator.service', 'convert'),
    'convert_text': ('src.logic.tools.byte_calculator.service', 'convert_text'),
    'format_number': ('src.logic.tools.byte_calculator.service', 'format_number'),
    'parse_number': ('src.logic.tools.byte_calculator.service', 'parse_number')}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
