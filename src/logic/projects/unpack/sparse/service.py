from __future__ import annotations

import os

from src.core.file_types import gettype
from src.logic.projects.unpack.models import UnpackCandidate

from .models import UnpackModuleSpec, UnpackRequest


def _shared_unpack():
    from src.logic.projects.unpack.workflow.service import unpack as shared_unpack
    return shared_unpack


FORMAT = 'sparse'
SPEC = UnpackModuleSpec(key='sparse', description='android sparse image', delegate_format='img')


def scan_candidates(work: str) -> list[UnpackCandidate]:
    result: list[UnpackCandidate] = []
    for file_name in os.listdir(work):
        if not file_name.endswith('.img'):
            continue
        item_name = file_name[:-4]
        if item_name == 'super':
            continue
        file_path = os.path.join(work, file_name)
        if gettype(file_path) != 'sparse':
            continue
        result.append(UnpackCandidate(name=item_name, detected_type='sparse'))
    return result


def build_request(selected) -> UnpackRequest:
    return UnpackRequest(selected=list(selected), format_name=SPEC.key, delegate_format=SPEC.delegate_format)


def run(selected, unpack_func=None):
    request = build_request(selected)
    target_unpack = unpack_func or _shared_unpack()
    return target_unpack(request.selected, request.delegate_format)
