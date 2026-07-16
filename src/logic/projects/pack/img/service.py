from __future__ import annotations
from .models import PackOutputRequest, PackOutputSpec

SPEC = PackOutputSpec(key='raw', description='pack raw image output')
def apply_output(request: PackOutputRequest, *, output=None):
    return True
