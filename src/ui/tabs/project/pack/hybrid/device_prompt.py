from __future__ import annotations

from src.ui.tabs.project.pack.hybrid import device_prompt_keys as keys
from src.ui.localization import LocalizationCatalog
from src.ui.common.controls import input_


def prompt_target_device(master: object, *, texts: LocalizationCatalog) -> str | None:
    """Ask the user for the target device identifier."""
    value = input_(
        texts=texts,
        title=texts.resolve_required_ui_text(keys.PROJECT_PACK_HYBRID_DEVICE_PROMPT_DEVICE_CODENAME_PROMPT),
        text="olive",
        master=master,
    )
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


__all__ = ["prompt_target_device"]
