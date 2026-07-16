from __future__ import annotations

import os
from src.core.selinux_audit_allow import main as selinux_audit_allow
from src.logic.tools.allow_selinux_audit.models import SelinuxAuditAllowRequest, SelinuxAuditValidationError


def build_request(*, log_path: str, output_dir: str) -> SelinuxAuditAllowRequest:
    return SelinuxAuditAllowRequest(
        log_path=str(log_path or '').strip(),
        output_dir=str(output_dir or '').strip(),
    )


def validate_request(
    request: SelinuxAuditAllowRequest,
    *,
    file_exists=os.path.isfile,
    dir_exists=os.path.isdir,
) -> SelinuxAuditValidationError | None:
    if not request.log_path:
        return SelinuxAuditValidationError.LOG_PATH_REQUIRED
    if not file_exists(request.log_path):
        return SelinuxAuditValidationError.LOG_FILE_NOT_FOUND
    if not request.output_dir:
        return SelinuxAuditValidationError.OUTPUT_DIR_REQUIRED
    if not dir_exists(request.output_dir):
        return SelinuxAuditValidationError.OUTPUT_DIR_NOT_FOUND
    return None


def run_selinux_audit_allow(log_path: str, output_dir: str):
    return selinux_audit_allow(log_path, output_dir)


def execute_request(request: SelinuxAuditAllowRequest):
    return run_selinux_audit_allow(request.log_path, request.output_dir)


__all__ = [
    'SelinuxAuditAllowRequest',
    'SelinuxAuditValidationError',
    'build_request',
    'execute_request',
    'run_selinux_audit_allow',
    'validate_request',
]
