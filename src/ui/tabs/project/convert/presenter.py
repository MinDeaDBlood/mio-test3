from __future__ import annotations


def replace_list_items(view, items: list[str]) -> None:
    view.list_b.clear()
    for item in items:
        view.list_b.insert(item, item)


def apply_candidate_group(view, result: tuple[str, list[str]]) -> None:
    source_format, items = result
    if hasattr(view.h, 'set') and view.h.get() != source_format:
        view.h.set(source_format)
    replace_list_items(view, items)


__all__ = ['apply_candidate_group', 'replace_list_items']
