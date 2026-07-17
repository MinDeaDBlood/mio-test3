"""Window and lifecycle boundary for the Plugin Store feature."""

from __future__ import annotations

from dataclasses import dataclass, field


import logging


from src.app.runtime.contexts.contracts import PresenceWindowProtocol
from src.app.plugins.store.runtime import PluginStoreRuntimeContext


class PluginStoreWindowSession:
    def __init__(
        self,
        *,
        runtime: PluginStoreRuntimeContext,
        window: PresenceWindowProtocol,
        logger: logging.Logger | None = None,
    ) -> None:
        self.runtime = runtime
        self.window = window
        self.logger = logger or logging.getLogger(__name__)
        self.host_window = runtime.host_window
        self.plugin_gateway = runtime.plugin_gateway
        self.presence = runtime.presence

    @staticmethod
    def focus_existing(runtime: PluginStoreRuntimeContext) -> bool:
        return runtime.presence.focus_existing()

    def open(self) -> None:
        self.presence.mark_open(self.window)

    def close(self) -> None:
        self.presence.mark_closed(self.window)

    def ensure_background_plugin_load(self) -> None:
        try:
            if self.plugin_gateway.claim_background_load():
                self.runtime.task_runner.fire_and_forget(
                    self.plugin_gateway.load_plugins_and_notify
                )
        except Exception:
            self.logger.exception(
                "PluginStoreWindowSession.ensure_background_plugin_load"
            )


@dataclass
class PluginStoreOperationState:
    """Application state for background Plugin Store operations."""

    tasks: set[str] = field(default_factory=set)
    fetch_inflight: bool = False

    def start_task(self, plugin_id: str) -> bool:
        if plugin_id in self.tasks:
            return False
        self.tasks.add(plugin_id)
        return True

    def finish_task(self, plugin_id: str) -> bool:
        if plugin_id not in self.tasks:
            return False
        self.tasks.remove(plugin_id)
        return True

    def start_fetch(self) -> bool:
        if self.fetch_inflight:
            return False
        self.fetch_inflight = True
        return True

    def finish_fetch(self) -> bool:
        was_inflight = self.fetch_inflight
        self.fetch_inflight = False
        return was_inflight


__all__ = ["PluginStoreOperationState", "PluginStoreWindowSession"]
