from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SelinuxAuditValidationError(Enum):
    LOG_PATH_REQUIRED = 'log_path_required'
    LOG_FILE_NOT_FOUND = 'log_file_not_found'
    OUTPUT_DIR_REQUIRED = 'output_dir_required'
    OUTPUT_DIR_NOT_FOUND = 'output_dir_not_found'


@dataclass(frozen=True)
class SelinuxAuditAllowRequest:
    log_path: str
    output_dir: str


__all__ = ['SelinuxAuditAllowRequest', 'SelinuxAuditValidationError']
