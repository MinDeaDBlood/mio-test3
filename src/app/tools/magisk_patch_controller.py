from __future__ import annotations

import os

from src.platform.filesystem import path_exists
from src.app.ui_tasks import UiTaskRunner
from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.tools.magisk_patch.service import (
    MagiskPatchRequest,
    build_output_path,
    get_arch,
    patch_boot_image,
    validate_inputs,
)


class MagiskPatchController:
    """Application boundary for Magisk boot image patching."""

    def __init__(
        self,
        *,
        cwd_path: str,
        temp_path: str,
        settings_obj,
        v_code_func,
        re_folder_func,
        task_runner: UiTaskRunner,
        output: ServiceOutput | None = None,
        logger=None,
    ) -> None:
        self._cwd_path = cwd_path
        self._temp_path = temp_path
        self._settings = settings_obj
        self._v_code_func = v_code_func
        self._re_folder_func = re_folder_func
        self._task_runner = task_runner
        self._output = output or build_service_output()
        self._logger = logger

    def get_arches(self, apk_path: str) -> list[str]:
        return get_arch(apk_path, logger=self._logger)

    def validate(self, *, boot_file_path: str, magisk_apk_path: str) -> tuple[bool, str | None]:
        return validate_inputs(boot_file_path=boot_file_path, magisk_apk_path=magisk_apk_path)

    def _build_request(
        self,
        *,
        boot_file_path: str,
        magisk_apk_path: str,
        is_64bit: bool,
        keep_verity: bool,
        keep_force_encrypt: bool,
        recovery_mode: bool,
        arch: str,
    ) -> MagiskPatchRequest:
        local_path = os.path.join(self._temp_path, self._v_code_func())
        self._re_folder_func(local_path)
        return MagiskPatchRequest(
            boot_file_path=boot_file_path,
            magisk_apk_path=magisk_apk_path,
            tool_bin=self._settings.tool_bin,
            local_path=local_path,
            is_64bit=is_64bit,
            keep_verity=keep_verity,
            keep_force_encrypt=keep_force_encrypt,
            recovery_mode=recovery_mode,
            arch=arch,
        )

    def _patch(self, request: MagiskPatchRequest) -> str:
        output_path = build_output_path(
            self._cwd_path,
            request.boot_file_path,
            exists_func=path_exists,
            unique_suffix_func=self._v_code_func,
        )
        result = patch_boot_image(request, output_path=output_path, output=self._output)
        if result is None:
            raise RuntimeError('Magisk patching process did not produce an output file.')
        return result

    def start(
        self,
        *,
        boot_file_path: str,
        magisk_apk_path: str,
        is_64bit: bool,
        keep_verity: bool,
        keep_force_encrypt: bool,
        recovery_mode: bool,
        arch: str,
        on_success,
        on_error,
    ) -> None:
        request = self._build_request(
            boot_file_path=boot_file_path,
            magisk_apk_path=magisk_apk_path,
            is_64bit=is_64bit,
            keep_verity=keep_verity,
            keep_force_encrypt=keep_force_encrypt,
            recovery_mode=recovery_mode,
            arch=arch,
        )
        self._task_runner.run(
            self._patch,
            request,
            on_success=on_success,
            on_error=on_error,
            exclusive=True,
        )


__all__ = ['MagiskPatchController']
