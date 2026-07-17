"""Uninstall lifecycle controller for the Plugin Store window."""

from __future__ import annotations


import logging

from src.app.plugins.store.host_port import PluginStoreHostPort
from src.logic.plugins.uninstall.result import PluginUninstallResult


class PluginStoreUninstallController:
    """Run plugin uninstall work and normalize results for UI state."""

    def __init__(
        self,
        *,
        host_port: PluginStoreHostPort,
        logger: logging.Logger | None = None,
    ) -> None:
        self.host_port = host_port
        self.logger = logger or logging.getLogger(__name__)

    def start(self, plugin_id: str) -> bool:
        try:
            self.host_port.task_runner.run(
                self._uninstall_worker,
                plugin_id,
                on_success=lambda result: self._apply_result(plugin_id, result),
                on_error=lambda exc: self._apply_error(plugin_id, exc),
            )
            return True
        except (RuntimeError, TypeError, ValueError) as exc:
            self._apply_error(plugin_id, exc)
            return False

    def _uninstall_worker(self, plugin_id: str) -> PluginUninstallResult:
        return self.host_port.plugin_gateway.uninstall(plugin_id)

    def _apply_result(
        self,
        plugin_id: str,
        result: PluginUninstallResult,
    ) -> None:
        self.host_port.apply_uninstall_result(plugin_id, result)

    def _apply_error(self, plugin_id: str, exc: Exception) -> None:
        self.logger.exception(
            'PluginStoreUninstallController.start: uninstall failed for %s',
            plugin_id,
        )
        self._apply_result(plugin_id, self._failure_result(exc))

    @staticmethod
    def _failure_result(exc: Exception) -> PluginUninstallResult:
        return False, str(exc), []


__all__ = ['PluginStoreUninstallController']
