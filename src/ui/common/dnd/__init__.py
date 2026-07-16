from __future__ import annotations

from importlib import import_module

__all__ = [
    'ASK',
    'CF_HDROP',
    'CF_TEXT',
    'CF_UNICODETEXT',
    'COPY',
    'DND_ALL',
    'DND_FILES',
    'DND_TEXT',
    'FileGroupDescriptor',
    'FileGroupDescriptorW',
    'LINK',
    'MOVE',
    'NONE',
    'PRIVATE',
    'REFUSE_DROP',
    'Tk',
]


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(name)
    module_name = '.TkinterDnD' if name == 'Tk' else '.tkinterdnd2_build_in'
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
