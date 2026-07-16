from __future__ import annotations
import os

def validate_request(work_output: str, partition_name: str) -> bool:
    if not work_output or not partition_name:
        return False
    return os.path.exists(os.path.join(work_output, f'{partition_name}.img'))
