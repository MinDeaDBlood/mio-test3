"""Lazy UI window launchers used across application and logic boundaries."""

from __future__ import annotations

from typing import Any


def open_pack_super_window() -> Any:
    from src.app.composition.super_pack import open_super_pack_window
    return open_super_pack_window()


def open_pack_payload_window(*, system_name: str | None = None):
    from src.app.composition.payload_pack import open_payload_pack_window
    return open_payload_pack_window(system_name=system_name)


__all__ = ["open_pack_super_window", "open_pack_payload_window"]
