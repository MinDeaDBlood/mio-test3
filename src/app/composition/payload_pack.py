from __future__ import annotations

from src.app.projects.payload_pack import PayloadPackLaunchResult
from src.app.localization_runtime import lang
from src.logic.projects.pack.payload.service import get_capability
from src.ui.tabs.project.pack.payload.window import PayloadPackUnavailableWindow


def open_payload_pack_window(
    *, system_name: str | None = None
) -> PayloadPackLaunchResult:
    capability = get_capability(system_name)
    if not capability.available:
        window = PayloadPackUnavailableWindow(texts=lang, reason=capability.reason)
        return PayloadPackLaunchResult(
            opened=False, capability=capability, window=window
        )
    raise RuntimeError(
        "Payload packing capability is available, but no payload pack UI is registered."
    )


__all__ = ["open_payload_pack_window"]
