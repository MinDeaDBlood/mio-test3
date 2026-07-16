from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from src.app.ui_tasks import UiTaskRunner
from src.logic.tools.mtk_port_tool import (
    MtkPortProfile,
    MtkPortRequest,
    MtkPortResult,
    MtkPortService,
)


class MtkPortController:
    """Application controller for the MTK port workflow."""

    def __init__(self, *, service: MtkPortService, task_runner: UiTaskRunner) -> None:
        self._service = service
        self._task_runner = task_runner

    def profiles(self) -> tuple[MtkPortProfile, ...]:
        return self._service.profiles()

    def start(
        self,
        *,
        profile_name: str,
        boot_image: str,
        system_image: str,
        port_rom: str,
        enabled_flags: Mapping[str, bool],
        output_as_image: bool,
        patch_magisk: bool,
        magisk_apk: str | None,
        target_arch: str,
        on_success: Callable[[MtkPortResult], None],
        on_error: Callable[[Exception], None],
        on_finally: Callable[[], None] | None = None,
    ) -> None:
        request = MtkPortRequest(
            profile_name=profile_name,
            boot_image=Path(boot_image),
            system_image=Path(system_image),
            port_rom=Path(port_rom),
            enabled_flags=dict(enabled_flags),
            output_as_image=output_as_image,
            patch_magisk=patch_magisk,
            magisk_apk=Path(magisk_apk) if magisk_apk else None,
            target_arch=target_arch,
        )
        self._task_runner.run(
            self._service.execute,
            request,
            on_success=on_success,
            on_error=on_error,
            on_finally=on_finally,
            exclusive=True,
        )


__all__ = ["MtkPortController"]
