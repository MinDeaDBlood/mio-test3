from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.platform.runtime_paths import PROJECT_ROOT


@dataclass(frozen=True, slots=True)
class MtkPortSourceDefaults:
    boot_image: str = ""
    system_image: str = ""


def detect_mtk_port_source_defaults(
    base_directory: str | Path = PROJECT_ROOT / "base",
) -> MtkPortSourceDefaults:
    base = Path(base_directory)
    boot = base / "boot.img"
    system = base / "system.img"
    return MtkPortSourceDefaults(
        boot_image=str(boot.resolve()) if boot.is_file() else "",
        system_image=str(system.resolve()) if system.is_file() else "",
    )


__all__ = ["MtkPortSourceDefaults", "detect_mtk_port_source_defaults"]
