"""Presence registry for the Plugin Store window."""

from __future__ import annotations

from typing import Protocol

from src.app.runtime.contexts.contracts import PresenceWindowProtocol


class PluginStoreStateBagProtocol(Protocol):
    active_mpk_store_instance: PresenceWindowProtocol | None
    mpk_store: bool


class PluginStorePresenceRegistry:
    def __init__(self, states: PluginStoreStateBagProtocol) -> None:
        self._states = states

    def focus_existing(self) -> bool:
        active = self._states.active_mpk_store_instance
        if active is None:
            return False
        window = active
        try:
            if not window.winfo_exists():
                return False
            window.lift()
            window.focus_force()
            return True
        except Exception:
            return False

    def mark_open(self, window: PresenceWindowProtocol) -> None:
        self._states.mpk_store = True
        self._states.active_mpk_store_instance = window

    def mark_closed(self, window: PresenceWindowProtocol) -> None:
        if self._states.active_mpk_store_instance is window:
            self._states.active_mpk_store_instance = None
        self._states.mpk_store = False


__all__ = ['PluginStorePresenceRegistry', 'PluginStoreStateBagProtocol']
