from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PostInstallEntry:
    partition: str
    run_postinstall: bool = False
    postinstall_path: str = ''
    filesystem_type: str = ''
    postinstall_optional: bool = False


__all__ = ['PostInstallEntry']
