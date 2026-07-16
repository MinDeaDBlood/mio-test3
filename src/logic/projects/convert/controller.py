from __future__ import annotations
from .models import ConvertSelection
from .validators import normalize_items, validate_format_pair

def build_selection(from_format: str, to_format: str, items: list[str]) -> ConvertSelection:
    return ConvertSelection(from_format=from_format, to_format=to_format, items=normalize_items(items))

def can_convert(from_format: str, to_format: str) -> bool:
    return validate_format_pair(from_format, to_format) and from_format != to_format
