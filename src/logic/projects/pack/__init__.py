"""Lazy public facade for pack registry helpers."""

from __future__ import annotations


def get_output_formats():
    from .registry import get_output_formats as _get_output_formats
    return _get_output_formats()


def apply_output_format(*args, **kwargs):
    from .registry import apply_output_format as _apply_output_format
    return _apply_output_format(*args, **kwargs)


__all__ = ['get_output_formats', 'apply_output_format']
