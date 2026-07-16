from __future__ import annotations

from importlib import import_module


def open_pack_super():
    return getattr(
        import_module("src.ui.tabs.project.pack.super.window"), "PackSuper"
    )()


PackSuper: object
pack_super: object

__all__ = ["PackSuper", "pack_super", "open_pack_super"]


def __getattr__(name: str):
    if name == "PackSuper":
        value = getattr(import_module("src.ui.tabs.project.pack.super.window"), name)
    elif name == "pack_super":
        value = getattr(import_module("src.logic.projects.pack.super.service"), name)
    else:
        raise AttributeError(name)
    globals()[name] = value
    return value
