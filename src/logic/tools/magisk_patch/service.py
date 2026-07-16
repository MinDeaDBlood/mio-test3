from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from src.core.Magisk import Magisk_patch
from src.logic.common.service_output import ServiceOutput, build_service_output


@dataclass(frozen=True)
class MagiskPatchRequest:
    boot_file_path: str
    magisk_apk_path: str
    tool_bin: str
    local_path: str
    is_64bit: bool
    keep_verity: bool
    keep_force_encrypt: bool
    recovery_mode: bool
    arch: str


def get_arch(apk_path: str, *, logger=None) -> list[str]:
    if not apk_path:
        raise ValueError('Magisk APK path is required.')
    if not os.path.isfile(apk_path):
        raise FileNotFoundError(f'Magisk APK does not exist: {apk_path}')
    try:
        with Magisk_patch(None, None, None, None, MAGISAPK=apk_path) as patcher:
            architectures = list(patcher.get_arch() or ())
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile):
        if logger is not None:
            logger.exception('Failed to read architectures from Magisk APK %s', apk_path)
        raise
    if not architectures:
        raise ValueError(f'No supported architectures were found in Magisk APK: {apk_path}')
    return architectures


def build_output_path(cwd_path: str, boot_file_path: str, *, exists_func=os.path.exists, unique_suffix_func=None) -> str:
    base_name = os.path.basename(boot_file_path)
    name_part = base_name
    for ext in ('.img', '.bin'):
        if base_name.lower().endswith(ext):
            name_part = base_name[:-len(ext)]
            break
    output_file = os.path.join(cwd_path, f'{name_part}_magisk_patched.img')
    if exists_func(output_file) and unique_suffix_func is not None:
        output_file = os.path.join(cwd_path, f'{name_part}_{unique_suffix_func()}_magisk_patched.img')
    return output_file


def validate_inputs(*, boot_file_path: str, magisk_apk_path: str) -> tuple[bool, str | None]:
    if not boot_file_path or not os.path.exists(boot_file_path):
        return False, 'Boot image not selected or not found.'
    if not magisk_apk_path or not os.path.exists(magisk_apk_path):
        return False, 'Magisk APK not selected or not found.'
    return True, None


def validate_request(request: MagiskPatchRequest) -> tuple[bool, str | None]:
    return validate_inputs(
        boot_file_path=request.boot_file_path,
        magisk_apk_path=request.magisk_apk_path,
    )


def patch_boot_image(
    request: MagiskPatchRequest,
    *,
    output_path: str,
    output: ServiceOutput | None = None,
) -> str | None:
    service_output = output or build_service_output()
    with Magisk_patch(
        request.boot_file_path,
        None,
        f'{request.tool_bin}/magiskboot',
        request.local_path,
        request.is_64bit,
        request.keep_verity,
        request.keep_force_encrypt,
        request.recovery_mode,
        request.magisk_apk_path,
        request.arch,
        output_sink=lambda message: service_output.log(message),
    ) as patcher:
        patcher.auto_patch()
        if patcher.output:
            os.rename(patcher.output, output_path)
            return output_path
    return None
