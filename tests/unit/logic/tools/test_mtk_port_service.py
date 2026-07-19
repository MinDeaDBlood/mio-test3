from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import sys
from pathlib import Path
from zipfile import BadZipFile

import pytest

from src.logic.common.service_output import build_service_output
from src.logic.tools.mtk_port_tool.models import MtkPortRequest
from src.logic.tools.mtk_port_tool.operation import (
    MtkPortBinaries,
    MtkPortOperation,
    MtkPortOperationError,
)
from src.logic.tools.mtk_port_tool.service import MtkPortService


def _request(tmp_path: Path, *, profile: str = "demo") -> MtkPortRequest:
    boot = tmp_path / "boot.img"
    system = tmp_path / "system.img"
    rom = tmp_path / "port.zip"
    for path in (boot, system, rom):
        path.write_bytes(b"data")
    return MtkPortRequest(
        profile_name=profile,
        boot_image=boot,
        system_image=system,
        port_rom=rom,
        enabled_flags={"replace_kernel": True},
        output_as_image=False,
        patch_magisk=False,
        magisk_apk=None,
        target_arch="arm64-v8a",
    )


def _resources(tmp_path: Path) -> dict[str, object]:
    return {
        "binaries": MtkPortBinaries(
            make_ext4fs=str(tmp_path / "make_ext4fs"),
            magiskboot=str(tmp_path / "magiskboot"),
            img2simg=str(tmp_path / "img2simg"),
        ),
        "update_binary_path": tmp_path / "update-binary",
        "local_runtime_dir": tmp_path / "local",
    }


def test_service_builds_operation_from_immutable_request(tmp_path: Path) -> None:
    calls: dict[str, object] = {}

    class Operation:
        def __init__(
            self,
            config,
            boot,
            system,
            rom,
            output_as_image,
            *,
            output,
            binaries,
            update_binary_path,
            local_runtime_dir,
        ):
            calls.update(
                config=config,
                binaries=binaries,
                update_binary_path=update_binary_path,
                local_runtime_dir=local_runtime_dir,
                boot=boot,
                system=system,
                rom=rom,
                output_as_image=output_as_image,
                output=output,
            )

        def start(self):
            calls["started"] = True

    events = []
    output = build_service_output(emit=events.append)
    service = MtkPortService(
        **_resources(tmp_path),
        profiles={
            "demo": {"flags": {"replace_kernel": False}, "replace": {"kernel": []}}
        },
        port_factory=Operation,
        output_directory=tmp_path / "out",
        output=output,
    )

    result = service.execute(_request(tmp_path))

    assert calls["started"] is True
    assert calls["config"]["flags"] == {"replace_kernel": True}
    assert calls["output"] is output
    assert result.output_directory == (tmp_path / "out").resolve()


def test_service_rejects_unknown_profile_before_constructing_operation(
    tmp_path: Path,
) -> None:
    service = MtkPortService(**_resources(tmp_path), profiles={})
    with pytest.raises(ValueError, match="Unknown MTK port profile"):
        service.execute(_request(tmp_path, profile="missing"))


def test_operation_rejects_invalid_port_archive(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    request = _request(tmp_path)
    operation = MtkPortOperation(
        {"flags": {}, "replace": {}, "partitions": []},
        str(request.boot_image),
        str(request.system_image),
        str(request.port_rom),
        output=build_service_output(emit=lambda _event: None),
        **_resources(tmp_path),
    )
    with pytest.raises(BadZipFile, match="valid ZIP"):
        operation.start()


def test_operation_raises_on_failed_external_command(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    request = _request(tmp_path)
    operation = MtkPortOperation(
        {"flags": {}, "replace": {}, "partitions": []},
        str(request.boot_image),
        str(request.system_image),
        str(request.port_rom),
        output=build_service_output(emit=lambda _event: None),
        **_resources(tmp_path),
    )
    with pytest.raises(MtkPortOperationError, match="exit code 3"):
        operation.execv([sys.executable, "-c", "raise SystemExit(3)"])


def test_operation_orchestrates_stages_in_order_and_cleans_after_success() -> None:
    operation = MtkPortOperation.__new__(MtkPortOperation)
    operation.genimg = False
    calls: list[str] = []
    operation._decompress_portzip = lambda: calls.append("decompress")
    operation._port_boot = lambda: (calls.append("boot"), True)[1]
    operation._port_system = lambda: (calls.append("system"), True)[1]
    operation._pack_rom = lambda: calls.append("pack_rom")
    operation._pack_img = lambda: calls.append("pack_img")
    operation.clean = lambda: calls.append("clean")

    operation.start()

    assert calls == ["decompress", "boot", "system", "pack_rom", "clean"]


def test_operation_uses_image_packaging_when_requested() -> None:
    operation = MtkPortOperation.__new__(MtkPortOperation)
    operation.genimg = True
    calls: list[str] = []
    operation._decompress_portzip = lambda: calls.append("decompress")
    operation._port_boot = lambda: (calls.append("boot"), True)[1]
    operation._port_system = lambda: (calls.append("system"), True)[1]
    operation._pack_rom = lambda: calls.append("pack_rom")
    operation._pack_img = lambda: calls.append("pack_img")
    operation.clean = lambda: calls.append("clean")

    operation.start()

    assert calls == ["decompress", "boot", "system", "pack_img", "clean"]


def test_operation_does_not_package_or_clean_after_failed_stage() -> None:
    operation = MtkPortOperation.__new__(MtkPortOperation)
    operation.genimg = False
    calls: list[str] = []
    operation._decompress_portzip = lambda: calls.append("decompress")
    operation._port_boot = lambda: (calls.append("boot"), False)[1]
    operation._port_system = lambda: (calls.append("system"), True)[1]
    operation._pack_rom = lambda: calls.append("pack_rom")
    operation._pack_img = lambda: calls.append("pack_img")
    operation.clean = lambda: calls.append("clean")

    with pytest.raises(MtkPortOperationError, match="boot porting failed"):
        operation.start()

    assert calls == ["decompress", "boot"]


def test_system_port_replacement_creates_missing_target_parents(
    tmp_path: Path, monkeypatch
) -> None:
    from hashlib import md5

    monkeypatch.chdir(tmp_path)
    boot = tmp_path / "boot.img"
    system = tmp_path / "system.img"
    rom = tmp_path / "port.zip"
    boot.write_bytes(b"boot")
    system.write_bytes(b"system-image")
    rom.write_bytes(b"rom")

    base_file = tmp_path / "base/system/vendor/lib64/hw/example.so"
    base_file.parent.mkdir(parents=True)
    base_file.write_bytes(b"base-library")
    (tmp_path / "base/system.md5").write_text(
        md5(system.read_bytes()).hexdigest(), encoding="utf-8"
    )
    (tmp_path / "tmp/rom/system").mkdir(parents=True)

    operation = MtkPortOperation(
        {
            "flags": {"replace_library": True},
            "replace": {"library": ["vendor/lib64/hw/example.so"]},
            "partitions": [],
        },
        str(boot),
        str(system),
        str(rom),
        output=build_service_output(emit=lambda _event: None),
        **_resources(tmp_path),
    )

    assert operation._port_system() is True
    assert (
        tmp_path / "tmp/rom/system/vendor/lib64/hw/example.so"
    ).read_bytes() == b"base-library"


def test_system_port_does_not_cache_md5_when_extraction_fails(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    boot = tmp_path / "boot.img"
    system = tmp_path / "system.img"
    rom = tmp_path / "port.zip"
    boot.write_bytes(b"boot")
    system.write_bytes(b"system-image")
    rom.write_bytes(b"rom")

    class FailingExtractor:
        def main(self, *_args, **_kwargs):
            raise RuntimeError("synthetic extraction failure")

    monkeypatch.setattr(
        "src.logic.tools.mtk_port_tool.system_port.Extractor", FailingExtractor
    )
    operation = MtkPortOperation(
        {"flags": {}, "replace": {}, "partitions": []},
        str(boot),
        str(system),
        str(rom),
        output=build_service_output(emit=lambda _event: None),
        **_resources(tmp_path),
    )

    with pytest.raises(RuntimeError, match="synthetic extraction failure"):
        operation._port_system()

    assert not (tmp_path / "base/system.md5").exists()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
