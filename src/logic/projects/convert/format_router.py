from __future__ import annotations
from .models import INPUT_FORMATS, OUTPUT_FORMATS

def get_input_formats() -> tuple[str, ...]:
    return INPUT_FORMATS

def get_output_formats() -> tuple[str, ...]:
    return OUTPUT_FORMATS

def is_dat_family(format_name: str) -> bool:
    return format_name in {'dat', 'br', 'xz'}
