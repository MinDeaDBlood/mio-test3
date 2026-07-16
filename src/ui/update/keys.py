from __future__ import annotations

WINDOW_TITLE = "update_window_title"
BRAND_LABEL = "update_window_brand_label"
CHECK_UPDATES_BUTTON = "update_window_check_updates_button"
CANCEL_BUTTON = "update_window_cancel_button"
GIT_NOT_INSTALLED_MESSAGE = "update_window_git_not_installed_message"

UPDATE_PRESENTER_APPLYING_UPDATE_PACKAGE = 'update_presenter_applying_update_package'
UPDATE_PRESENTER_CHECK_UPDATES = 'update_presenter_check_updates'
UPDATE_PRESENTER_DEVICE_UPDATES_NOT_FOUND = 'update_presenter_device_updates_not_found'
UPDATE_PRESENTER_DOWNLOAD_FAILED_NETWORK = 'update_presenter_download_failed_network'
UPDATE_PRESENTER_FETCHING_DATA = 'update_presenter_fetching_data'
UPDATE_PRESENTER_LATEST_VERSION = 'update_presenter_latest_version'
UPDATE_PRESENTER_NEW_VERSION_FORMAT = 'update_presenter_new_version_format'
UPDATE_PRESENTER_RETRY = 'update_presenter_retry'
UPDATE_PRESENTER_UPDATE_DOWNLOAD_FAILED = 'update_presenter_update_download_failed'
UPDATE_PRESENTER_UPDATE_FAILED = 'update_presenter_update_failed'
UPDATE_PRESENTER_UPDATE_NOW = 'update_presenter_update_now'
UPDATE_PRESENTER_UPDATE_PARSE_FAILED = 'update_presenter_update_parse_failed'
UPDATE_PRESENTER_UPDATING = 'update_presenter_updating'

UPDATE_WINDOW_CHECK_UPDATES_HINT = 'update_window_check_updates_hint'
UPDATE_WINDOW_UPDATE_INFORMATION = 'update_window_update_information'

__all__ = [name for name in globals() if name.isupper()]
