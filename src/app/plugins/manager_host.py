"""Lazy application host for the Plugin Manager tab."""

from __future__ import annotations

import logging

from src.app.startup_metrics import FeatureTimeline


class PluginManagerHost:
    """Own lazy Plugin Manager construction without storing state on the Tk window."""

    def __init__(self, window) -> None:
        self._window = window
        self._manager = None

    def ensure_manager(self):
        manager = self._manager
        if manager is not None:
            try:
                if manager.winfo_exists():
                    return manager
            except Exception:
                logging.exception("Cannot inspect the existing Plugin Manager window")

        from src.app.composition.plugin_manager import create_plugin_manager_view

        timeline = FeatureTimeline("plugin_manager_open")
        manager = create_plugin_manager_view(
            master=self._window.tab7,
            host_window=self._window,
        )
        manager.gui()
        self._manager = manager
        timeline.log(logger=logging)
        return manager

    def handle_tab_changed(self, _event: object | None = None):
        try:
            selected = self._window.notepad.select()
        except Exception:
            logging.exception("Cannot read the selected main tab")
            return None
        if selected == str(self._window.tab7):
            return self.ensure_manager()
        return None

    def install(self) -> None:
        self._window.notepad.bind(
            "<<NotebookTabChanged>>",
            self.handle_tab_changed,
            add="+",
        )
        try:
            if self._window.notepad.select() == str(self._window.tab7):
                self._window.after_idle(self.ensure_manager)
        except Exception:
            logging.exception("Cannot schedule initial Plugin Manager construction")


def install_lazy_plugin_manager_host(window) -> PluginManagerHost:
    host = PluginManagerHost(window)
    host.install()
    return host


__all__ = ["PluginManagerHost", "install_lazy_plugin_manager_host"]
