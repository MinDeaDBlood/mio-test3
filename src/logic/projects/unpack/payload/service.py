from __future__ import annotations

import os

from src.logic.projects.unpack.models import UnpackCandidate

from .models import UnpackModuleSpec, UnpackRequest


def _shared_unpack():
    from src.logic.projects.unpack.workflow.service import unpack as shared_unpack
    return shared_unpack


SPEC = UnpackModuleSpec(key='payload', description='payload.bin partitions')


def payload_reader(*args, **kwargs):
    from src.core.payload_manifest import payload_reader as _payload_reader
    return _payload_reader(*args, **kwargs)


def scan_candidates(work: str) -> list[UnpackCandidate]:
    payload_path = os.path.join(work, 'payload.bin')
    if not os.path.exists(payload_path):
        return []
    with open(payload_path, 'rb') as payload_stream:
        return [
            UnpackCandidate(name=partition.partition_name, size_bytes=partition.new_partition_info.size)
            for partition in payload_reader(payload_stream).partitions
        ]


def build_request(selected) -> UnpackRequest:
    return UnpackRequest(selected=list(selected), format_name=SPEC.key)


def run(selected, unpack_func=None):
    request = build_request(selected)
    target_unpack = unpack_func or _shared_unpack()
    return target_unpack(request.selected, request.format_name)
