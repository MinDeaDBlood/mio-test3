from __future__ import annotations

WINDOW_TITLE = "plugins_store_window_plugin"
INSTALLATION_COMPLETE_BUTTON = "plugins_store_button_state_installation_complete"
INSTALL_BUTTON = "plugins_store_button_state_install"
REPOSITORY_PARSE_ERROR_MESSAGE = "plugins_store_catalog_repository_parse_error_message"
REPOSITORY_PARSE_ERROR_DIALOG_TITLE = (
    "plugins_store_catalog_repository_parse_error_dialog_title"
)
DEPENDENCY_NOT_FOUND_MESSAGE_FORMAT = (
    "plugins_store_install_dependency_not_found_message_format"
)
DEPENDENCY_NOT_FOUND_DIALOG_TITLE = (
    "plugins_store_install_dependency_not_found_dialog_title"
)
DEPENDENCY_INSTALL_FAILED_MESSAGE_FORMAT = (
    "plugins_store_install_dependency_failed_message_format"
)
DEPENDENCY_INSTALL_FAILED_DIALOG_TITLE = (
    "plugins_store_install_dependency_failed_dialog_title"
)
PLUGIN_INSTALL_FAILED_MESSAGE_FORMAT = (
    "plugins_store_install_plugin_failed_message_format"
)
PLUGIN_INSTALL_FAILED_DIALOG_TITLE = "plugins_store_install_plugin_failed_dialog_title"
LAYOUT_HEADING = "plugins_store_layout_plugin"
REFRESH_BUTTON = "plugins_store_layout_refresh"
DOWNLOAD_FAILED_LABEL = "plugins_store_install_download_failed_label"
DOWNLOAD_ERROR_DIALOG_TITLE = "plugins_store_install_download_error_dialog_title"
UNINSTALL_ERROR_DIALOG_TITLE = "plugins_store_uninstall_error_dialog_title"
CATALOG_AUTHOR_LABEL = "plugins_store_catalog_view_model_author_label"
CATALOG_VERSION_LABEL = "plugins_store_catalog_view_model_version_label"
CATALOG_SIZE_LABEL = "plugins_store_catalog_view_model_image_size_label"

PLUGINS_STORE_BUTTON_STATE_INSTALL = 'plugins_store_button_state_install'
PLUGINS_STORE_BUTTON_STATE_READY = 'plugins_store_button_state_ready'
PLUGINS_STORE_BUTTON_STATE_UNINSTALL = 'plugins_store_button_state_uninstall'

PLUGINS_STORE_CATALOG_VIEW_MODEL_INSTALL = 'plugins_store_catalog_view_model_install'
PLUGINS_STORE_CATALOG_VIEW_MODEL_UNINSTALL = 'plugins_store_catalog_view_model_uninstall'

PLUGINS_STORE_LAYOUT_PLUGIN_REPOSITORY_URL = 'plugins_store_layout_plugin_repository_url'

__all__ = [name for name in globals() if name.isupper()]
