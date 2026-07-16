from __future__ import annotations

import os.path as op
from os import unlink
from pathlib import Path
from shutil import rmtree
from zipfile import BadZipFile, ZipFile

from src.core.Magisk import Magisk_patch
from src.core.mtk_port.files import BootImageWorkspace, PropertyFile
from src.logic.tools.mtk_port_tool.operation_base import MtkPortOperationError


class MtkBootPortMixin:
    def _port_boot(self) -> bool:
        def replace(src: Path, dest: Path):
            self._log(f"Replace boot {src} -> {dest}...")
            return dest.write_bytes(src.read_bytes())

        basedir = Path("tmp/base")
        portdir = Path("tmp/port")
        self._log("Mkdir boot port directory")
        if basedir.exists():
            rmtree(basedir)
        if portdir.exists():
            rmtree(portdir)
        basedir.mkdir(parents=True)
        portdir.mkdir(parents=True)

        self._log("Copy/Unzip images")
        basedir.joinpath("boot.img").absolute().write_bytes(
            Path(self.bootimg).read_bytes()
        )
        base = basedir.joinpath("boot.img")
        try:
            ZipFile(self.portzip, "r").extract("boot.img", "tmp/port/")
        except (BadZipFile, KeyError, OSError) as exc:
            raise MtkPortOperationError(
                "Port ROM does not contain a readable boot.img in its root"
            ) from exc
        port = Path(portdir.joinpath("boot.img").absolute())

        self._log("Unpacks boot Image")
        BootImageWorkspace(base).unpack()
        BootImageWorkspace(port).unpack()

        for item, item_flag in self.items["flags"].items():
            if not item_flag:
                continue
            if item == "replace_kernel":
                for path in self.items["replace"]["kernel"]:
                    if basedir.joinpath(path).exists():
                        self._log(f"Replaces kernel {path}")
                        replace(
                            basedir.joinpath(path),
                            portdir.joinpath(path).absolute(),
                        )
            elif item == "replace_fstab":
                for path in self.items["replace"]["fstab"]:
                    if basedir.joinpath(path).exists():
                        self._log(f"Replaces part tables {path}")
                        replace(
                            basedir.joinpath(path),
                            portdir.joinpath(path).absolute(),
                        )
            elif item == "selinux_permissive":
                boot_info = portdir.joinpath("bootinfo.txt")
                if boot_info.exists():
                    with boot_info.open("r+") as stream:
                        lines = [line.rstrip() for line in stream.readlines()]
                        if any(
                            "androidboot.selinux=permissive" in line for line in lines
                        ):
                            self._log("selinux is permissive already，do nothing.")
                            continue
                        stream.seek(0)
                        stream.truncate(0)
                        for line in lines:
                            if line.startswith("cmdline:"):
                                self._log("set selinux permissive")
                                stream.write(line + " androidboot.selinux=permissive\n")
                            else:
                                stream.write(line + "\n")
            elif item == "enable_adb":
                default_prop = portdir.joinpath("inidrd/default.prop")
                if default_prop.exists():
                    self._log("open adb and debug")
                    with PropertyFile(str(default_prop)) as prop:
                        for key, value in (
                            ("ro.secure", "0"),
                            ("ro.adb.secure", "0"),
                            ("ro.debuggable", "1"),
                            ("persist.sys.usb.config", "mtp,adb"),
                        ):
                            prop.set(key, value)

        self._log("Repacks boot image")
        BootImageWorkspace(str(port)).repack()
        target = Path("tmp/rom/boot.img")
        replace(Path(portdir.joinpath("boot-new.img")), target)
        if self.items.get("patch_magisk"):
            if op.isfile(self.items.get("magisk_apk")):
                with Magisk_patch(
                    str(target),
                    "",
                    self.binaries.magiskboot,
                    str(self.local_runtime_dir),
                    MAGISAPK=self.items["magisk_apk"],
                    PATCH_ARCH=self.items["target_arch"],
                    output_sink=lambda text: self.output.log(text),
                ) as patcher:
                    patcher.auto_patch()
                    if patcher.output:
                        replace(Path(patcher.output), target)
                        unlink(patcher.output)
            else:
                self._log(f"{self.items['magisk_apk']} not found")
        return True


__all__ = ["MtkBootPortMixin"]
