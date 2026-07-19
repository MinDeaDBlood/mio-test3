from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import BOTH, HORIZONTAL, LEFT, X, Label, Menu, StringVar, ttk

from src.ui.localization import LocalizationCatalog
from src.ui.contracts import ClosableBinding
from src.ui.tabs.plugins.execution import collect_plugin_values
from src.ui.tabs.plugins.manager.catalog import PluginManagerCatalogPresenter
from src.ui.tabs.plugins.manager import keys
from src.ui.tabs.plugins.plugin_new_dialog import PluginNewDialog
from src.ui.tabs.tools.icon_grid import IconGrid


class MpkMan(ttk.Frame):
    """Plugin-manager view. All operations are delegated to the app controller."""

    def __init__(
        self,
        *,
        master,
        texts: LocalizationCatalog,
        host_window,
        runtime,
        controller,
        choose_file: Callable[..., str],
        show_info: Callable[[str], object],
        open_store: Callable[[], object],
        open_installer: Callable[[str], object],
        open_editor: Callable[[object], object],
    ):
        super().__init__(master=master)
        self._texts = texts
        self.host_window = host_window
        self.runtime = runtime
        self.controller = controller
        self.choose_file = choose_file
        self.show_info = show_info
        self.open_store = open_store
        self.open_installer = open_installer
        self.open_editor = open_editor
        self.pack(padx=10, pady=10, fill=BOTH, expand=True)
        self.chosen = StringVar(value="")
        self.images_: dict[str, object] = {}
        self.catalog = PluginManagerCatalogPresenter(self, logger=logging)
        self._plugin_event_binding: ClosableBinding | None = None
        self._catalog_generation = 0

    def message_pop(self, *args, **kwargs):
        return self.host_window.message_pop(*args, **kwargs)

    def run_plugin(self, plugin_id: str):
        cancelled, values = collect_plugin_values(
            self.controller.plugin_config_path(plugin_id),
            texts=self._texts,
            config_service=self.controller.config_service,
            choose_file=lambda: self.choose_file(),
            show_error=lambda message: self.message_pop(message, "red"),
        )
        if not cancelled:
            self.controller.run_plugin(plugin_id, values)

    def list_plugins(self):
        return self.refresh()

    def refresh(self):
        self._catalog_generation += 1
        generation = self._catalog_generation
        return self.controller.load_catalog_async(
            on_success=lambda result: self._apply_catalog(generation, result),
            on_error=lambda error: self._handle_catalog_error(generation, error),
        )

    def _apply_catalog(self, generation: int, result) -> None:
        if generation != self._catalog_generation or not self.winfo_exists():
            return
        self.catalog.render(result)

    def _handle_catalog_error(self, generation: int, error: Exception) -> None:
        if generation != self._catalog_generation or not self.winfo_exists():
            return
        logging.error("Plugin catalog loading failed: %s", error)

    def popup(self, name, event):
        self.chosen.set(name)
        self.rmenu2.post(event.x_root, event.y_root)

    def edit_plugin(self, plugin_id: str):
        if not plugin_id:
            self.message_pop(
                self._texts.resolve_required_ui_text(keys.NO_PLUGIN_SELECTED_MESSAGE),
                title=self._texts.resolve_required_ui_text(
                    keys.NO_PLUGIN_SELECTED_DIALOG_TITLE
                ),
                color="orange",
            )
            return
        try:
            self.open_editor(self.controller.prepare_editor_target(plugin_id))
        except Exception as exc:
            logging.exception("Plugin editor launch failed: %s", plugin_id)
            self.message_pop(
                str(exc),
                title=self._texts.resolve_required_ui_text(
                    keys.EDITOR_LAUNCH_ERROR_DIALOG_TITLE
                ),
                color="red",
            )

    def uninstall_plugin(self, plugin_id: str):
        if not plugin_id:
            return
        self.controller.uninstall_plugin(
            plugin_id, on_success=self._finalize_uninstall_plugin
        )

    def _finalize_uninstall_plugin(self, result):
        ok, message, _removed = result
        if not self.winfo_exists():
            return
        if not ok and message:
            self.message_pop(
                message,
                title=self._texts.resolve_required_ui_text(
                    keys.UNINSTALL_ERROR_DIALOG_TITLE
                ),
                color="orange",
            )
        self.refresh()

    def install_mpk(self):
        path = self.choose_file(
            title=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_SELECT_PLUGIN_TITLE),
            filetypes=((self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_PLUGIN_FILE_TYPE), "*.mpk"),),
        )
        if not path:
            return
        result, _reason = self.controller.check_mpk(path)
        if result == self.runtime.module_error_codes.Normal:
            self.open_installer(path)

    def create_plugin(self):
        PluginNewDialog(
            self.controller,
            texts=self._texts,
            open_editor=self.open_editor,
            show_info=self.show_info,
        )

    def attach_event_binding(self, binding: ClosableBinding) -> None:
        if self._plugin_event_binding is not None:
            raise RuntimeError("Plugin event binding is already attached")
        self._plugin_event_binding = binding

    def consume_plugin_events(self, events) -> None:
        if self.winfo_exists() and any(event.refresh_manager for event in events):
            self.refresh()

    def _on_destroy(self, event=None):
        if event is None or event.widget is self:
            if self._plugin_event_binding is not None:
                self._plugin_event_binding.close()
                self._plugin_event_binding = None

    def gui(self):
        self.bind("<Destroy>", self._on_destroy, add="+")

        header = ttk.Frame(self)
        header.pack(fill=X)
        ttk.Label(
            header,
            text=self._texts.resolve_required_ui_text(keys.HEADER_LABEL),
            font=(None, 20),
        ).pack(padx=10, pady=10, side=LEFT)
        ttk.Button(
            header,
            text=self._texts.resolve_required_ui_text(keys.OPEN_STORE_BUTTON),
            command=self.open_store,
        ).pack(side="right", padx=10, pady=10)
        ttk.Separator(self, orient=HORIZONTAL).pack(padx=10, pady=(0, 5), fill=X)

        plugins_label = Label(
            self, text=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_PLUGIN_CONTEXT_MENU_HINT)
        )
        plugins_label.pack(padx=5, pady=(5, 0), anchor="nw")
        self.pls = IconGrid(self)
        self.pls.pack(padx=5, pady=5, fill=BOTH, expand=True)

        menu = Menu(self, tearoff=False, borderwidth=0)
        menu.add_command(
            label=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_INSTALL), command=self.install_mpk
        )
        menu.add_command(
            label=self._texts.resolve_required_ui_text(keys.REFRESH_BUTTON),
            command=self.refresh,
        )
        menu.add_command(
            label=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_NEW), command=self.create_plugin
        )
        plugins_label.bind(
            "<Button-3>", lambda event: menu.post(event.x_root, event.y_root)
        )
        self.pls.canvas.bind(
            "<Button-3>", lambda event: menu.post(event.x_root, event.y_root)
        )

        self.rmenu2 = Menu(self, tearoff=False, borderwidth=0)
        self.rmenu2.add_command(
            label=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_UNINSTALL),
            command=lambda: self.uninstall_plugin(self.chosen.get()),
        )
        self.rmenu2.add_command(
            label=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_RUN),
            command=lambda: self.run_plugin(self.chosen.get()),
        )
        self.rmenu2.add_command(
            label=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_EXPORT),
            command=lambda: self.controller.export_plugin(self.chosen.get()),
        )
        self.rmenu2.add_command(
            label=self._texts.resolve_required_ui_text(keys.PLUGINS_MANAGER_WINDOW_EDIT),
            command=lambda: self.edit_plugin(self.chosen.get()),
        )
        # The real page is complete before any filesystem/catalog work starts.
        # Catalog I/O returns through the UI dispatcher and never delays the
        # first painted Plugins frame.
        self.refresh()
        self.controller.ensure_background_load()


__all__ = ["MpkMan"]
