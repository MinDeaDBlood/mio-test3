from __future__ import annotations

from src.logic.projects.convert.controller import build_selection
from src.logic.projects.convert.service import choose_candidate_group, convert_selection, list_candidates


class ConvertController:
    """Application controller for conversion candidate loading and execution."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def list_candidates(self, source_format: str) -> list[str]:
        return list_candidates(source_format, runtime=self._runtime)

    def choose_candidate_group(self, preferred_format: str) -> tuple[str, list[str]]:
        return choose_candidate_group(preferred_format, runtime=self._runtime)

    def convert(self, source_format: str, target_format: str, items: list[str]):
        selection = build_selection(source_format, target_format, items)
        return convert_selection(selection, runtime=self._runtime)


__all__ = ['ConvertController']
