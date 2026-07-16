from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ImageProcessingOperations:
    get_type: Callable[[str], str]
    is_empty_image: Callable[[str], bool]
    simg2img: Callable[[str], Any]
    lpunpack_get_info: Callable[[str], Any]
    lpunpack_unpack: Callable[..., Any]
    normalize_super_outputs: Callable[[str], Any]
    unpack_dtbo: Callable[..., Any]
    unpack_boot: Callable[..., Any]
    logo_dump: Callable[..., Any]
    logo_dumper_cls: type
    vbpatch_cls: type
    romfs_parse_cls: type
    guoke_logo_cls: type
    aml_main: Callable[..., Any]
    call: Callable[..., Any]
    extract_ext_image: Callable[..., Any]
    extract_erofs_image: Callable[..., Any]
    extract_f2fs_image: Callable[..., Any]
    runtime_output: Callable[[Any], Any]
    extract_gpt_image: Callable[..., Any] = lambda *_args, **_kwargs: False
    extract_splash_image: Callable[..., Any] = lambda *_args, **_kwargs: False


@dataclass(frozen=True)
class ImageHandlerContext:
    runtime: Any
    work: str
    partition_name: str
    image_path: str
    parts: dict
    json_edit: Any
    output: Any
    operations: ImageProcessingOperations


__all__ = ['ImageHandlerContext', 'ImageProcessingOperations']
