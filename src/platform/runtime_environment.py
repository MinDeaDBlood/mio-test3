from __future__ import annotations

import os
import platform
from enum import Enum


class RuntimeWarningCode(str, Enum):
    NON_ROOT_POSIX = "non-root-posix"
    LOONGARCH64 = "loongarch64"


def detect_runtime_warning_codes() -> tuple[RuntimeWarningCode, ...]:
    warnings: list[RuntimeWarningCode] = []
    if os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() != 0:
        warnings.append(RuntimeWarningCode.NON_ROOT_POSIX)
    if platform.machine() == "loongarch64":
        warnings.append(RuntimeWarningCode.LOONGARCH64)
    return tuple(warnings)


__all__ = ["RuntimeWarningCode", "detect_runtime_warning_codes"]
