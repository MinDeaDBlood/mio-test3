from __future__ import annotations
from .validators import normalize_selection
from . import service

def execute(selected, unpack_func=None):
    normalized = normalize_selection(selected)
    if not normalized:
        return False
    return service.run(normalized, unpack_func=unpack_func)

def list_candidates(work: str) -> list[str]:
    return service.scan_candidates(work)

def get_format_name() -> str:
    return service.SPEC.key
