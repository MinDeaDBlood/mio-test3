from __future__ import annotations

from src.ui.localization import LocalizationCatalog
from src.ui.welcome import navigation_keys as keys
from src.ui.welcome.layout import (
    WELCOME_PAGE_LAYOUTS,
    WelcomeContentProtocol,
    WelcomePageLayout,
    WelcomeWindowProtocol,
    WelcomeWindowSize,
    compute_content_wrap_width,
    compute_welcome_window_size,
    fit_welcome_window,
    get_page_layout,
    release_welcome_window,
)
from src.ui.welcome.navigation_presenter import WelcomeNavigationLabels


def get_labels(texts: LocalizationCatalog) -> WelcomeNavigationLabels:
    return WelcomeNavigationLabels(
        back=texts.resolve_required_ui_text(keys.BACK_BUTTON),
        next=texts.resolve_required_ui_text(keys.NEXT_BUTTON),
        finish=texts.resolve_required_ui_text(keys.FINISH_BUTTON),
    )


__all__ = [
    "WELCOME_PAGE_LAYOUTS",
    "WelcomeContentProtocol",
    "WelcomePageLayout",
    "WelcomeWindowProtocol",
    "WelcomeWindowSize",
    "compute_content_wrap_width",
    "compute_welcome_window_size",
    "fit_welcome_window",
    "get_labels",
    "get_page_layout",
    "release_welcome_window",
]
