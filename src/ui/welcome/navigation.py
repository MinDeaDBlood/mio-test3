from __future__ import annotations

from src.ui.localization import LocalizationCatalog
from src.ui.welcome import navigation_keys as keys
from src.ui.welcome.layout import (
    WelcomeContentProtocol,
    WelcomeWindowProtocol,
    WelcomeWindowSize,
    compute_welcome_window_size,
    fit_welcome_window,
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
    'WelcomeContentProtocol',
    'WelcomeWindowProtocol',
    'WelcomeWindowSize',
    'compute_welcome_window_size',
    'fit_welcome_window',
    'get_labels',
    'release_welcome_window',
]
