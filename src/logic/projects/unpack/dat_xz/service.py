from __future__ import annotations

import os

from src.core.file_types import gettype
from src.logic.projects.unpack.models import UnpackCandidate

from .models import UnpackModuleSpec, UnpackRequest


def _shared_unpack():
    from src.logic.projects.unpack.workflow.service import unpack as shared_unpack
    return shared_unpack


FORMAT = 'new.dat.xz'
SPEC = UnpackModuleSpec(key='new.dat.xz', description='xz compressed dat image')


def scan_candidates(work: str) -> list[UnpackCandidate]:
    result: list[UnpackCandidate] = []
    for file_name in os.listdir(work):
        if not file_name.endswith(FORMAT):
            continue
        item_name = file_name.split(f'.{FORMAT}')[0]
        file_type = gettype(os.path.join(work, file_name))
        if file_type == 'unknown':
            file_type = FORMAT
        result.append(UnpackCandidate(name=item_name, detected_type=file_type))
    return result


def build_request(selected) -> UnpackRequest:
    return UnpackRequest(selected=list(selected), format_name=SPEC.key)


def run(selected, unpack_func=None):
    request = build_request(selected)
    target_unpack = unpack_func or _shared_unpack()
    return target_unpack(request.selected, request.format_name)
