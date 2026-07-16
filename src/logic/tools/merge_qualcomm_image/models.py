from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class MergeQualcommRequest:
    rawprogram_xml: str
    partition_name: str
    output_path: str


class MergeQualcommValidationError(Enum):
    RAWPROGRAM_NOT_FOUND = 'rawprogram_not_found'
    OUTPUT_PATH_REQUIRED = 'output_path_required'


@dataclass(frozen=True)
class MergeQualcommResult:
    succeeded: bool
    error: MergeQualcommValidationError | None = None
    details: str = ''


__all__ = ['MergeQualcommRequest', 'MergeQualcommResult', 'MergeQualcommValidationError']
