from __future__ import annotations

import os
from src.core.qsb_imger import process_by_xml


from src.logic.tools.merge_qualcomm_image.models import MergeQualcommRequest, MergeQualcommResult, MergeQualcommValidationError


def validate_request(request: MergeQualcommRequest) -> MergeQualcommValidationError | None:
    if not os.path.isfile(request.rawprogram_xml):
        return MergeQualcommValidationError.RAWPROGRAM_NOT_FOUND
    if not str(request.output_path or '').strip():
        return MergeQualcommValidationError.OUTPUT_PATH_REQUIRED
    return None


def execute_merge(request: MergeQualcommRequest) -> MergeQualcommResult:
    validation_error = validate_request(request)
    if validation_error is not None:
        return MergeQualcommResult(False, error=validation_error)
    os.makedirs(request.output_path, exist_ok=True)
    try:
        process_by_xml(request.rawprogram_xml, request.partition_name, request.output_path)
    except (OSError, RuntimeError, ValueError) as exc:
        return MergeQualcommResult(False, details=str(exc))
    return MergeQualcommResult(True)


__all__ = [
    'MergeQualcommRequest',
    'MergeQualcommResult',
    'MergeQualcommValidationError',
    'execute_merge',
    'validate_request',
]
