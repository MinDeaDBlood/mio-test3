from __future__ import annotations

import os

from src.core import lpunpack
from src.core.file_types import gettype
from src.logic.projects.unpack.models import UnpackCandidate

from .models import UnpackModuleSpec, UnpackRequest


def _shared_unpack():
    from src.logic.projects.unpack.workflow.service import unpack as shared_unpack
    return shared_unpack


SPEC = UnpackModuleSpec(key='super', description='super image partitions')


def scan_candidates(work: str) -> list[UnpackCandidate]:
    image_path = os.path.join(work, 'super.img')
    if not os.path.exists(image_path):
        return []
    if gettype(image_path) not in {'super', 'sparse'}:
        return []
    return [UnpackCandidate(name=item) for item in lpunpack.get_parts(image_path) or []]


def build_request(selected) -> UnpackRequest:
    return UnpackRequest(selected=list(selected), format_name=SPEC.key)


def run(selected, unpack_func=None):
    request = build_request(selected)
    target_unpack = unpack_func or _shared_unpack()
    return target_unpack(request.selected, request.format_name)
