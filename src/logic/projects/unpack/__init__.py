"""Lazy public facade for unpack registry helpers."""

from __future__ import annotations


def get_available_formats():
    from .registry import get_available_formats as _get_available_formats
    return _get_available_formats()


def list_candidates(*args, **kwargs):
    from .registry import list_candidates as _list_candidates
    return _list_candidates(*args, **kwargs)


def run_unpack(*args, **kwargs):
    from .registry import run_unpack as _run_unpack
    return _run_unpack(*args, **kwargs)


__all__ = ['get_available_formats', 'list_candidates', 'run_unpack']
