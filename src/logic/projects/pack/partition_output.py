from __future__ import annotations

from typing import Callable

from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity, ServiceOutput

_CONVERTIBLE_OUTPUT_FORMATS = frozenset({'dat', 'br', 'sparse'})


def is_sparse_output_requested(output_format: str) -> bool:
    """Return whether the selected output format needs final image conversion."""
    return output_format in _CONVERTIBLE_OUTPUT_FORMATS


def finalize_partition_output(
    *,
    output_format: str,
    output_dir: str,
    partition_name: str,
    brotli_level: int | str,
    dat_version: int | str,
    apply_output_format_func: Callable,
    output: ServiceOutput,
) -> bool:
    """Finalize a packed partition and publish a semantic completion event."""
    if output_format in _CONVERTIBLE_OUTPUT_FORMATS:
        if not apply_output_format_func(
            output_format,
            output_dir,
            partition_name,
            brotli_level=int(brotli_level),
            dat_version=int(dat_version),
            output=output,
        ):
            return False
    output.log(
        message('created', 'Created: {item}', item=partition_name),
        severity=OutputSeverity.SUCCESS,
    )
    return True


__all__ = [
    'finalize_partition_output',
    'is_sparse_output_requested',
]
