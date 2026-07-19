"""Lazy application host for the Plugin Manager tab."""

from __future__ import annotations

import logging
from tkinter import ttk

from src.app.startup_metrics import FeatureTimeline
from src.app.ui_feedback import build_ui_dispatcher
from src.app.ui_tasks import build_ui_task_runner


class PluginManagerHost:
    """Own lazy Plugin Manager construction without storing state on the Tk window."""

    def __init__(self, window) -> None:
        self._window = window
        self._manager = None
        self._manager_factory = None
        self._preload_started = False
        self._placeholder = None
        self._manager_revealed = False
        dispatcher = build_ui_dispatcher(host_window=window)
        self._preload_runner = build_ui_task_runner(
            dispatcher=dispatcher,
            is_alive=window.winfo_exists,
            logger=logging,
        )

    def _ensure_placeholder(self):
        placeholder = self._placeholder
        if placeholder is not None:
            try:
                if placeholder.winfo_exists():
                    return placeholder
            except Exception:
                logging.exception("Cannot inspect the Plugin Manager placeholder")
        # This is a real themed page surface, not a captured image or a color
        # overlay.  It is ready before the tab can be selected, so the notebook
        # never exposes the native background while lazy modules are imported.
        placeholder = ttk.Frame(self._window.tab7)
        placeholder.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._placeholder = placeholder
        return placeholder

    @staticmethod
    def _load_manager_factory():
        from src.app.composition.plugin_manager import create_plugin_manager_view

        return create_plugin_manager_view

    def _start_preload(self) -> bool:
        if self._manager_factory is not None or self._preload_started:
            return False
        self._preload_started = True
        self._preload_runner.run(
            self._load_manager_factory,
            on_success=self._finish_preload,
            on_error=self._handle_preload_error,
        )
        return True

    def _finish_preload(self, factory) -> None:
        self._preload_started = False
        self._manager_factory = factory
        # Build the real page after the cold import, while another tab still
        # covers it. The first Plugins click then has no construction work.
        self._window.after_idle(self.ensure_manager)

    def _handle_preload_error(self, error: Exception) -> None:
        self._preload_started = False
        logging.error("Plugin Manager module preload failed: %s", error)

    def _selected_plugins_tab(self) -> bool:
        try:
            return self._window.notepad.selection_target() == str(
                self._window.tab7
            )
        except Exception:
            logging.exception("Cannot read the selected main tab")
            return False

    def ensure_manager(self):
        manager = self._manager
        if manager is not None:
            try:
                if manager.winfo_exists():
                    return manager
            except Exception:
                logging.exception("Cannot inspect the existing Plugin Manager window")

        factory = self._manager_factory
        if factory is None:
            self._ensure_placeholder()
            self._start_preload()
            return self._placeholder

        timeline = FeatureTimeline("plugin_manager_open")
        manager = factory(
            master=self._window.tab7,
            host_window=self._window,
        )
        manager.gui()
        self._manager = manager
        self._window.notepad.buffer_page(self._window.tab7)
        placeholder = self._placeholder
        if placeholder is not None:
            try:
                placeholder.lift()
            except Exception:
                logging.exception("Cannot cover the prepared Plugin Manager")
        self._window.notepad.invalidate_focusability(self._window.tab7)
        timeline.log(logger=logging)
        if self._selected_plugins_tab():
            self._window.after_idle(self._reveal_manager)
        return manager

    def _reveal_manager(self) -> None:
        if self._manager is None or not self._selected_plugins_tab():
            return
        try:
            self._manager.update_idletasks()
        except Exception:
            logging.exception("Cannot settle the prepared Plugin Manager")
        placeholder = self._placeholder
        self._placeholder = None
        if placeholder is not None:
            try:
                placeholder.destroy()
            except Exception:
                logging.exception("Cannot reveal the prepared Plugin Manager")
        self._manager_revealed = True

    def handle_tab_changed(self, _event: object | None = None):
        try:
            selection_target = getattr(self._window.notepad, "selection_target", None)
            selected = (
                selection_target()
                if callable(selection_target)
                else self._window.notepad.select()
            )
        except Exception:
            logging.exception("Cannot read the selected main tab")
            return None
        if selected == str(self._window.tab7):
            if self._manager is not None:
                if not self._manager_revealed:
                    self._reveal_manager()
                return self._manager
            placeholder = self._ensure_placeholder()
            # Publish the already painted target page first.  Construction is
            # queued behind the tab switch so a cold import never blocks the
            # button callback or exposes a partially populated page.
            self._window.after_idle(self.ensure_manager)
            self._window.after_idle(self._reveal_manager)
            self._start_preload()
            return placeholder
        return None

    def install(self) -> None:
        self._ensure_placeholder()
        self._window.notepad.bind(
            "<<NotebookTabChanging>>",
            self.handle_tab_changed,
            add="+",
        )
        # Preload Python modules outside the Tk thread.  This removes the
        # roughly half-second cold import from the first Plugins click without
        # moving any widget construction off the main thread.
        self._window.after_idle(self._start_preload)
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
