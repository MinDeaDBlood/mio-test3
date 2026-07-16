from __future__ import annotations

from importlib import import_module

__all__ = ['PackOutputRequest', 'PackOutputSpec', 'validate_request', 'SPEC', 'apply_output', 'execute', 'get_output_format']

_EXPORT_MODULES = {
    'PackOutputRequest': '.models',
    'PackOutputSpec': '.models',
    'validate_request': '.validators',
    'SPEC': '.service',
    'apply_output': '.service',
    'execute': '.controller',
    'get_output_format': '.controller',
}

def __getattr__(name: str):
    try:
        relative_module = _EXPORT_MODULES[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    module = import_module(relative_module, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value

