from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.logic.common.service_output import ServiceOutput, build_service_output
from src.ui.common.service_output import UiServiceOutputSink
from src.ui.localization import LocalizationCatalog


def build_ui_service_output(
    *,
    texts: LocalizationCatalog,
    log: Callable[[str], Any] | None = None,
    notify: Callable[..., Any] | None = None,
) -> ServiceOutput:
    sink = UiServiceOutputSink(log=log or print, texts=texts, notify=notify)
    return build_service_output(emit=sink)


__all__ = ['build_ui_service_output']
