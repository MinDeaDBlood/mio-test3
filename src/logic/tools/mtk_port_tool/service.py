from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Callable, Mapping, Protocol

from src.logic.common.service_output import ServiceOutput, build_service_output
from src.logic.tools.mtk_port_tool.models import (
    MtkPortProfile,
    MtkPortRequest,
    MtkPortResult,
)
from src.logic.tools.mtk_port_tool.operation import MtkPortBinaries, MtkPortOperation
from src.logic.tools.mtk_port_tool.profiles import (
    default_support_chipset_profiles,
    validate_support_chipset_profiles,
)


class MtkPortExecutable(Protocol):
    def start(self) -> None: ...


PortFactory = Callable[..., MtkPortExecutable]


class MtkPortService:
    """Build and execute one MTK port operation from an immutable request."""

    def __init__(
        self,
        *,
        binaries: MtkPortBinaries,
        update_binary_path: Path,
        local_runtime_dir: Path,
        profiles: Mapping[str, dict] | None = None,
        port_factory: PortFactory = MtkPortOperation,
        output_directory: Path = Path("out"),
        output: ServiceOutput | None = None,
    ) -> None:
        source_profiles = (
            profiles if profiles is not None else default_support_chipset_profiles()
        )
        self._profiles = validate_support_chipset_profiles(source_profiles)
        self._binaries = binaries
        self._update_binary_path = update_binary_path
        self._local_runtime_dir = local_runtime_dir
        self._port_factory = port_factory
        self._output_directory = output_directory
        self._output = output or build_service_output()

    def profiles(self) -> tuple[MtkPortProfile, ...]:
        return tuple(
            MtkPortProfile.create(name=name, flags=data.get("flags", {}))
            for name, data in self._profiles.items()
        )

    def execute(self, request: MtkPortRequest) -> MtkPortResult:
        profile = self._profiles.get(request.profile_name)
        if profile is None:
            raise ValueError(f"Unknown MTK port profile: {request.profile_name}")

        for label, path in (
            ("boot image", request.boot_image),
            ("system image", request.system_image),
            ("port ROM", request.port_rom),
        ):
            if not path.is_file():
                raise FileNotFoundError(f"{label} does not exist: {path}")

        if request.patch_magisk:
            if request.magisk_apk is None or not request.magisk_apk.is_file():
                raise FileNotFoundError(
                    f"Magisk APK does not exist: {request.magisk_apk}"
                )

        operation_config = deepcopy(profile)
        profile_flags = operation_config.setdefault("flags", {})
        unknown_flags = set(request.enabled_flags) - set(profile_flags)
        if unknown_flags:
            names = ", ".join(sorted(unknown_flags))
            raise ValueError(
                f"Unknown flags for profile {request.profile_name}: {names}"
            )
        for name in profile_flags:
            profile_flags[name] = bool(request.enabled_flags.get(name, False))

        operation_config["patch_magisk"] = request.patch_magisk
        operation_config["magisk_apk"] = (
            str(request.magisk_apk) if request.magisk_apk is not None else ""
        )
        operation_config["target_arch"] = request.target_arch

        operation = self._port_factory(
            operation_config,
            str(request.boot_image),
            str(request.system_image),
            str(request.port_rom),
            request.output_as_image,
            output=self._output,
            binaries=self._binaries,
            update_binary_path=self._update_binary_path,
            local_runtime_dir=self._local_runtime_dir,
        )
        operation.start()
        return MtkPortResult(output_directory=self._output_directory.resolve())


__all__ = ["MtkPortService"]
