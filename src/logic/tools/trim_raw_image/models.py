from dataclasses import dataclass
from enum import Enum


class TrimRawValidationError(Enum):
    PATH_REQUIRED = 'path_required'
    FILE_NOT_FOUND = 'file_not_found'


@dataclass(frozen=True)
class TrimRawImageResult:
    trimmed_bytes: int


__all__ = ['TrimRawImageResult', 'TrimRawValidationError']
