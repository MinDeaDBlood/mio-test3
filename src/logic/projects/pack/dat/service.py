from __future__ import annotations

from src.core.sparse_tools import img2simg
from src.logic.projects.pack.filesystem_service import datbr

from .models import PackOutputRequest, PackOutputSpec

SPEC = PackOutputSpec(key='dat', description='pack dat output')


def apply_output(request: PackOutputRequest, *, output=None):
    image_path = f"{request.work_output}{request.partition_name}.img"
    img2simg(image_path)
    return datbr(request.work_output, request.partition_name, 'dat', int(request.dat_version), output=output)
