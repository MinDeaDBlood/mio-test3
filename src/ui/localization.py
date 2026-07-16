from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LocalizationCatalog(Protocol):
    """Read-only presentation text contract supplied by application composition."""

    def resolve(
        self,
        *keys: str,
        default: str = '',
        context: str = 'optional',
        use_reference_language: bool | None = None,
    ) -> str: ...

    def resolve_optional(self, *keys: str, default: str = '') -> str: ...

    def resolve_ui_text(self, *keys: str) -> str: ...

    def resolve_required_ui_text(self, *keys: str) -> str: ...

    def current_language(self) -> str | None: ...

    def current_language_file(self) -> str | None: ...


__all__ = ['LocalizationCatalog']
