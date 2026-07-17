from __future__ import annotations

from collections.abc import Callable

from tkinter import BOTH, BOTTOM, DISABLED, LEFT, Text, X
from tkinter import ttk

from src.ui.common.windowing import Toplevel
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.plugins import module_dialogs_keys as keys


class PluginUninstallDialog(Toplevel):
    def __init__(
        self,
        controller,
        plugin_id: str,
        *,
        texts: LocalizationCatalog,
        show_message: Callable[..., object],
        wait: bool = False,
    ):
        super().__init__()
        self._texts = texts
        self.controller = controller
        self.show_message = show_message
        self.arr: dict[str, str] = {}
        self.uninstall_b = None
        self.wait = wait
        self.value = plugin_id
        self.value2 = None
        self.check_pass = False
        if plugin_id and controller.is_installed(plugin_id):
            self.check_pass = True
            self.value2 = controller.get_name(plugin_id)
            self.lsdep()
        elif plugin_id:
            self.value2 = plugin_id
        self.ask()

    def ask(self):
        self.title(self._texts.resolve_required_ui_text(keys.UNINSTALL_DIALOG_TITLE))
        content_frame = ttk.Frame(self)
        content_frame.pack(padx=15, pady=15, fill=BOTH, expand=True)
        display_name = (
            self.value2
            if self.value2
            else self.value
            or self._texts.resolve_required_ui_text(keys.UNINSTALL_UNKNOWN_PLUGIN_NAME)
        )
        if not self.value:
            message_text = self._texts.resolve_required_ui_text(
                keys.UNINSTALL_SELECTION_REQUIRED_MESSAGE
            )
        elif not self.check_pass:
            message_text = self._texts.resolve_required_ui_text(
                keys.UNINSTALL_PLUGIN_NOT_FOUND_FORMAT
            ).format(plugin_id=display_name)
        elif self.controller.is_virtual(self.value):
            message_text = self._texts.resolve_required_ui_text(
                keys.UNINSTALL_VIRTUAL_PLUGIN_FORMAT
            ).format(plugin_name=display_name)
        else:
            template = self._texts.resolve_required_ui_text(
                keys.UNINSTALL_CONFIRM_FORMAT
            )
            message_text = (
                template % display_name
                if "%s" in template
                else f"{template} {display_name}"
            )
        ttk.Label(
            content_frame, text=message_text, wraplength=400, justify="left"
        ).pack(fill=X, padx=5, pady=(0, 10))
        if self.arr:
            dep_frame = ttk.LabelFrame(
                content_frame,
                text=self._texts.resolve_required_ui_text(
                    keys.UNINSTALL_DEPENDENCIES_GROUP_TITLE
                ),
            )
            dep_frame.pack(fill=BOTH, expand=True, padx=5, pady=(0, 10))
            widget = Text(dep_frame, height=min(max(len(self.arr), 3), 12), wrap="word")
            widget.pack(fill=BOTH, expand=True, padx=5, pady=5)
            widget.insert("1.0", "\n".join(f"- {name}" for name in self.arr.values()))
            widget.config(state=DISABLED)
        buttons = ttk.Frame(content_frame)
        buttons.pack(fill=X, pady=(15, 0), side=BOTTOM)
        ttk.Button(
            buttons,
            text=self._texts.resolve_required_ui_text(keys.UNINSTALL_CANCEL_BUTTON),
            command=self.destroy,
        ).pack(fill=X, expand=True, side=LEFT, padx=(0, 5))
        if (
            self.check_pass
            and self.value
            and not self.controller.is_virtual(self.value)
        ):
            self.uninstall_b = ttk.Button(
                buttons,
                text=self._texts.resolve_required_ui_text(
                    keys.UNINSTALL_CONFIRM_BUTTON
                ),
                command=self.uninstall,
                style="Accent.TButton",
            )
            self.uninstall_b.pack(fill=X, expand=True, side=LEFT, padx=(5, 0))
        self.center_on_screen(force=True)
        if self.wait:
            self.wait_window()

    def lsdep(self):
        dependent_ids = self.controller.collect_dependent_plugin_ids(self.value)
        self.arr = {
            plugin_id: self.controller.get_name(plugin_id)
            for plugin_id in dependent_ids
        }

    def uninstall(self):
        if self.uninstall_b and self.uninstall_b.winfo_exists():
            self.uninstall_b.config(state="disabled")
        self.controller.uninstall_plugin(self.value, on_success=self._on_uninstalled)

    def _on_uninstalled(self, result):
        ok, message, _removed = result
        if not ok and message:
            self.show_message(
                message,
                title=self._texts.resolve_required_ui_text(
                    keys.UNINSTALL_ERROR_DIALOG_TITLE
                ),
                color="orange",
            )
        if self.winfo_exists():
            self.destroy()


__all__ = ["PluginUninstallDialog"]
