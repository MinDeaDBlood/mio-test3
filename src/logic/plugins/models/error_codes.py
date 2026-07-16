from __future__ import annotations

from enum import IntEnum


class ModuleErrorCodes(IntEnum):
    Normal = 0
    PlatformNotSupport = 1
    DependsMissing = 2
    IsBroken = 3
    ArchNotSupported = 4
    # GenericError is not recommended.
    GenericError = 9


__all__ = ['ModuleErrorCodes']
