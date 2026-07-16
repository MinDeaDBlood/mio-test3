from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .base import ImageHandlerContext
from .containers import handle_known_container
from .extractors import handle_extracted_image_type
from .preprocessors import convert_sparse_if_needed, run_partition_preprocessors


@dataclass(frozen=True)
class ImageHandlerRegistry:
    run_preprocessors: Callable[[ImageHandlerContext, str], bool | None]
    convert_sparse: Callable[[ImageHandlerContext, str], str]
    handle_container: Callable[[ImageHandlerContext, str], bool | None]
    handle_extractor: Callable[[ImageHandlerContext, str], bool | None]

    @classmethod
    def default(cls) -> 'ImageHandlerRegistry':
        return cls(
            run_preprocessors=run_partition_preprocessors,
            convert_sparse=convert_sparse_if_needed,
            handle_container=handle_known_container,
            handle_extractor=handle_extracted_image_type,
        )


__all__ = ['ImageHandlerRegistry']
