from __future__ import annotations
from .models import PackOutputRequest
from .validators import validate_request
from .service import apply_output, SPEC

def execute(work_output: str, partition_name: str, *, brotli_level: int = 0, dat_version: int = 4, output=None):
    if not validate_request(work_output, partition_name):
        return False
    request = PackOutputRequest(work_output=work_output, partition_name=partition_name, output_format=SPEC.key, brotli_level=brotli_level, dat_version=dat_version)
    return apply_output(request, output=output)

def get_output_format() -> str:
    return SPEC.key
