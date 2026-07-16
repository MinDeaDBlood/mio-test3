from __future__ import annotations

from collections.abc import Callable, Mapping

from src.ui.localization import LocalizationCatalog

from src.ui.tabs.plugins.plugin_config_dialog import PluginConfigDialog


def collect_plugin_values(
    config_path: str | None,
    *,
    texts: LocalizationCatalog,
    config_service,
    choose_file: Callable[[], str],
    show_error: Callable[[str], object],
) -> tuple[bool, Mapping[str, object]]:
    if config_path is None:
        return False, {}
    dialog = PluginConfigDialog(
        config_path,
        texts=texts,
        config_service=config_service,
        choose_file=choose_file,
        show_error=show_error,
    )
    values = {
        name: variable.get() if hasattr(variable, 'get') else variable
        for name, variable in dialog.values.items()
    }
    return dialog.cancelled, values


__all__ = ['collect_plugin_values']
