from __future__ import annotations

import logging

from importlib import import_module

from src.app.composition.dialogs import choose_file
from src.app.composition.editor import open_editor
from src.app.localization_runtime import lang
from src.app.plugins.manager_controller import PluginManagerController
from src.app.plugins.ui_event_binding import PluginUiEventBinding
from src.app.plugins.runtime import build_plugin_ui_runtime_context
from src.app.runtime.contexts.settings import resolve_settings
from src.app.composition.plugin_installer import open_plugin_installer
from src.app.ui_feedback import build_ui_notifier
from src.app.composition.service_output import build_ui_service_output
from src.ui.tabs.plugins.manager.window import MpkMan
from src.ui.warn.dialogs import info_win


def _open_plugin_editor(target):
    lexer = import_module('pygments.lexers').Python3Lexer if target.python_source else None
    return open_editor(str(target.directory), target.filename, lexer=lexer)


def create_plugin_manager_view(*, master, host_window):
    runtime = build_plugin_ui_runtime_context(host_window)
    notifier = build_ui_notifier(host_window=runtime.host_window)

    def notify_on_ui_thread(**kwargs):
        return runtime.dispatcher.dispatch(lambda: notifier.show(**kwargs))

    controller = PluginManagerController(
        runtime=runtime,
        settings=resolve_settings(),
        output=build_ui_service_output(texts=lang, notify=notify_on_ui_thread),
        logger=logging,
    )

    def open_store():
        from src.app.composition.plugin_store import open_plugin_store
        return open_plugin_store()

    view = MpkMan(
        master=master,
        texts=lang,
        host_window=runtime.host_window,
        runtime=runtime,
        controller=controller,
        choose_file=choose_file,
        show_info=info_win,
        open_store=open_store,
        open_installer=open_plugin_installer,
        open_editor=_open_plugin_editor,
    )
    view.attach_event_binding(
        PluginUiEventBinding(
            dispatcher=runtime.dispatcher,
            consume=view.consume_plugin_events,
            is_alive=view.winfo_exists,
            logger=logging,
        )
    )
    return view


__all__ = ['create_plugin_manager_view']
