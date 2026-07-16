from __future__ import annotations

from typing import Any

from src.logic.tools.mtk_port_tool.profiles import default_support_chipset_profiles
from src.platform.mtk_port_profile_repository import MtkPortProfileRepository


def load_or_create_mtk_port_profiles(
    repository: MtkPortProfileRepository | None = None,
) -> dict[str, dict[str, Any]]:
    """Load editable profiles or persist the domain defaults on first use."""

    resolved = repository or MtkPortProfileRepository()
    if resolved.exists():
        return resolved.load()
    profiles = default_support_chipset_profiles()
    resolved.save(profiles)
    return profiles


__all__ = ["load_or_create_mtk_port_profiles"]
