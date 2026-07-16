"""Lazy public facade for convert helpers."""

from __future__ import annotations


def build_selection(*args, **kwargs):
    from .controller import build_selection as _build_selection
    return _build_selection(*args, **kwargs)


def can_convert(*args, **kwargs):
    from .controller import can_convert as _can_convert
    return _can_convert(*args, **kwargs)


def list_candidates(*args, **kwargs):
    from .service import list_candidates as _list_candidates
    return _list_candidates(*args, **kwargs)


def convert_selection(*args, **kwargs):
    from .service import convert_selection as _convert_selection
    return _convert_selection(*args, **kwargs)


__all__ = ['build_selection', 'can_convert', 'list_candidates', 'convert_selection']
