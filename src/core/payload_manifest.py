from __future__ import annotations
from src.core.diagnostics import emit

import struct

from src.core import update_metadata_pb2 as um


def u64(x):
    return struct.unpack('>Q', x)[0]


def payload_reader(payloadfile):
    """Read payload.bin and return a DeltaArchiveManifest."""
    if payloadfile.read(4) != b'CrAU':
        emit("Magic Check Fail\n")
        payloadfile.close()
        return um
    file_format_version = u64(payloadfile.read(8))
    assert file_format_version == 2
    manifest_size = u64(payloadfile.read(8))
    metadata_signature_size = struct.unpack('>I', payloadfile.read(4))[0] if file_format_version > 1 else 0
    manifest = payloadfile.read(manifest_size)
    payloadfile.read(metadata_signature_size)
    dam = um.DeltaArchiveManifest()
    dam.ParseFromString(manifest)
    return dam


__all__ = ['u64', 'payload_reader']
