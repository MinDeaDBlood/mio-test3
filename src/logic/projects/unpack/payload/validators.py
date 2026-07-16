from __future__ import annotations

def normalize_selection(selected) -> list[str]:
    if not selected:
        return []
    return [str(item) for item in selected if str(item).strip()]

def has_selection(selected) -> bool:
    return bool(normalize_selection(selected))
