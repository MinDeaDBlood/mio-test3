from __future__ import annotations

from .validators import normalize_selection

_FORMAT_NAME = 'payload'


def execute(selected, unpack_func=None):
    normalized = normalize_selection(selected)
    if not normalized:
        return False
    from .service import run

    return run(normalized, unpack_func=unpack_func)


def list_candidates(work: str) -> list[str]:
    from .service import scan_candidates

    return scan_candidates(work)


def get_format_name() -> str:
    return _FORMAT_NAME
