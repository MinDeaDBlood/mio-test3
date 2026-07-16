from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class MtkPortProfile:
    name: str
    flags: Mapping[str, bool]

    @classmethod
    def create(cls, *, name: str, flags: Mapping[str, bool]) -> 'MtkPortProfile':
        return cls(name=name, flags=MappingProxyType(dict(flags)))


@dataclass(frozen=True)
class MtkPortRequest:
    profile_name: str
    boot_image: Path
    system_image: Path
    port_rom: Path
    enabled_flags: Mapping[str, bool]
    output_as_image: bool
    patch_magisk: bool
    magisk_apk: Path | None
    target_arch: str


@dataclass(frozen=True)
class MtkPortResult:
    output_directory: Path


__all__ = ['MtkPortProfile', 'MtkPortRequest', 'MtkPortResult']
