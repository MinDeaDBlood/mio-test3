from __future__ import annotations
from .models import INPUT_FORMATS, OUTPUT_FORMATS, ConvertSelection

def normalize_items(items) -> list[str]:
    if not items:
        return []
    return [str(item) for item in items if str(item).strip()]

def validate_format_pair(source: str, target: str) -> bool:
    return source in INPUT_FORMATS and target in OUTPUT_FORMATS

def validate_selection(selection: ConvertSelection) -> bool:
    return validate_format_pair(selection.from_format, selection.to_format) and bool(normalize_items(selection.items))
