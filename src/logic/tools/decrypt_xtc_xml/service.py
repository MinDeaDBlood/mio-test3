from __future__ import annotations

import os
from src.core.xtc_recovery_helper import decrypt as decrypt_xtc


from src.logic.tools.decrypt_xtc_xml.models import DecryptXtcValidationError


def normalize_path(path: str) -> str:
    return str(path or '').strip()


def validate_path(path: str, *, path_exists=os.path.exists) -> DecryptXtcValidationError | None:
    normalized = normalize_path(path)
    if not normalized:
        return DecryptXtcValidationError.PATH_REQUIRED
    if not path_exists(normalized):
        return DecryptXtcValidationError.PATH_NOT_FOUND
    return None


def decrypt_tree(path: str):
    normalized = normalize_path(path)
    for root, _, files in os.walk(normalized, topdown=True):
        for name in files:
            if name.endswith('.xml'):
                decrypt_xtc(os.path.join(root, name))


__all__ = ['DecryptXtcValidationError', 'decrypt_tree', 'normalize_path', 'validate_path']
