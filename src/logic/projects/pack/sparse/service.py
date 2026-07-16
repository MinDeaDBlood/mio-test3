from __future__ import annotations

from src.core.sparse_tools import img2simg
from src.logic.common.messages import message

from .models import PackOutputRequest, PackOutputSpec

SPEC = PackOutputSpec(key='sparse', description='pack sparse image output')


def apply_output(request: PackOutputRequest, *, output=None):
    image_path = f"{request.work_output}{request.partition_name}.img"
    if output is not None:
        output.log(message('converting_image', 'Converting image {item}', item=request.partition_name))
    img2simg(image_path)
    return True
