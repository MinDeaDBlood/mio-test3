from __future__ import annotations

import logging
from collections.abc import Callable

from src.platform.operation_logging import operation_context

logger = logging.getLogger(__name__)


class PluginLifecycleAdapter:
    """Executes registered plugin lifecycle callbacks at the platform boundary."""

    def __init__(
        self,
        *,
        run_entry: Callable[[object], object],
        before_pack_entry: object,
        packing_entry: object,
        shutdown_entry: object,
    ) -> None:
        self._run_entry = run_entry
        self._before_pack_entry = before_pack_entry
        self._packing_entry = packing_entry
        self._shutdown_entry = shutdown_entry

    def before_pack(self) -> None:
        self._execute("before_pack", self._before_pack_entry)

    def packing_started(self) -> None:
        self._execute("packing", self._packing_entry)

    def shutdown(self) -> None:
        self._execute("close", self._shutdown_entry)

    def _execute(self, event_name: str, entry: object) -> None:
        try:
            with operation_context("plugin.lifecycle", event=event_name):
                logger.info("plugin.lifecycle.started: event=%s", event_name)
                self._run_entry(entry)
                logger.info("plugin.lifecycle.completed: event=%s", event_name)
        except Exception:
            logger.exception("plugin.lifecycle.failed: event=%s", event_name)


def build_plugin_lifecycle_adapter(manager: object) -> PluginLifecycleAdapter:
    return PluginLifecycleAdapter(
        run_entry=manager.addon_loader.run_entry,
        before_pack_entry=manager.addon_entries.before_pack,
        packing_entry=manager.addon_entries.packing,
        shutdown_entry=manager.addon_entries.close,
    )


__all__ = ["PluginLifecycleAdapter", "build_plugin_lifecycle_adapter"]
