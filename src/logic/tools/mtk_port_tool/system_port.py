from __future__ import annotations

import glob
import os.path as op
from hashlib import md5
from pathlib import Path
from shutil import copytree, rmtree

from src.core.imgextractor import Extractor
from src.core.mtk_port.files import PropertyFile
from src.core.ota_dat import Sdat2img as sdat2img


class MtkSystemPortMixin:
    def _port_system(self) -> bool:
        def replace(value: str) -> None:
            self._log(f"Replaces {base_prefix}/{value} -> {port_prefix}/{value}...")
            if "*" in value:
                for file_path in glob.glob(op.join(str(base_prefix), value)):
                    relative = op.relpath(file_path, str(base_prefix))
                    self._log(f"\t$base/{relative} -> $port/{relative}")
                    target = port_prefix.joinpath(relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(base_prefix.joinpath(relative).read_bytes())
            elif base_prefix.joinpath(value).is_dir():
                target = port_prefix.joinpath(value)
                if target.exists():
                    rmtree(target)
                copytree(base_prefix.joinpath(value), target)
            else:
                target = port_prefix.joinpath(value)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(base_prefix.joinpath(value).read_bytes())

        self._log("Delect system md5 verifier.")
        with open(self.sysimg, "rb") as stream:
            digest = md5()
            for chunk in iter(lambda: stream.read(4096), b""):
                digest.update(chunk)
            system_md5 = digest.hexdigest()
        md5_path = Path("base/system.md5")
        recorded_text = md5_path.read_text() if md5_path.exists() else ""
        recorded_lines = recorded_text.splitlines()
        recorded_md5 = recorded_lines[0] if recorded_lines else ""

        unpack_required = not (
            system_md5 == recorded_md5 and Path("base/system").exists()
        )
        if not unpack_required:
            self._log("Delected system unpacked，skip unpacking.")
        else:
            md5_path.parent.mkdir(parents=True, exist_ok=True)
            system_path = Path("base/system")
            config_path = Path("base/config")
            if system_path.exists():
                rmtree(system_path)
            if config_path.exists():
                rmtree(config_path)
            self._log("Unpacking system image... ", end="")
            Extractor().main(self.sysimg, "base/system", "base")
            md5_path.write_text(system_md5)
            self._log("Done!")

        if Path("tmp/rom/system.new.dat").exists():
            self._log("Delected system.new.dat，Converting...")
            self.sdat = True
            with open("tmp/rom/system.transfer.list") as transfer:
                self.sdat_ver = int(transfer.readline().rstrip("\n"))
            sdat2img(
                "tmp/rom/system.transfer.list",
                "tmp/rom/system.new.dat",
                "tmp/rom/system.img",
            )
            self._log("Unpacking target system images...")
            Extractor().main("tmp/rom/system.img", "tmp/rom/system", "tmp/rom")

        base_prefix = Path("base/system")
        port_prefix = Path("tmp/rom/system")
        for item, item_flag in self.items["flags"].items():
            if not item_flag or item in {"replace_kernel", "replace_fstab"}:
                continue
            if item.startswith("replace_"):
                for path in self.items["replace"][item.split("_")[1]]:
                    if base_prefix.joinpath(path).exists() or "*" in path:
                        replace(path)
                    else:
                        self._log(
                            f"Warning: {path} not found in baserom，maybe its not a big problem"
                        )
                continue
            if item in {"single_simcard", "dual_simcard"}:
                single = item == "single_simcard"
                sim_type = "Single SimCard" if single else "Double SimCard"
                self._log(f"Modifying config [{sim_type}]")
                with PropertyFile(str(port_prefix.joinpath("build.prop"))) as prop:
                    for key, value in (
                        ("persist.multisim.config", "ss" if single else "dsds"),
                        ("persist.radio.multisim.config", "ss" if single else "dsds"),
                        ("ro.telephony.sim.count", "1" if single else "2"),
                        ("persist.dsds.enabled", "false" if single else "true"),
                        ("ro.dual.sim.phone", "false" if single else "true"),
                    ):
                        prop.set(key, value)
            elif item == "fit_density":
                self._log("Get dpi from base rom and write to port rom")
                with PropertyFile(str(port_prefix.joinpath("build.prop"))) as port_prop:
                    with PropertyFile(
                        str(base_prefix.joinpath("build.prop"))
                    ) as base_prop:
                        density = base_prop.get("ro.sf.lcd_density")
                        self._log(f"Modified port rom build.prop dpi:{density}")
                        port_prop.set("ro.sf.lcd_density", density)
            elif item in {"change_timezone", "change_locale", "change_model"}:
                key_groups = {
                    "timezone": ("persist.sys.timezone",),
                    "locale": ("ro.product.locale",),
                    "model": (
                        "ro.product.manufacturer",
                        "ro.build.product",
                        "ro.product.model",
                        "ro.product.device",
                        "ro.product.board",
                        "ro.product.brand",
                    ),
                }
                change_type = item.split("_")[1]
                with PropertyFile(str(port_prefix.joinpath("build.prop"))) as port_prop:
                    with PropertyFile(
                        str(base_prefix.joinpath("build.prop"))
                    ) as base_prop:
                        for key in key_groups[change_type]:
                            value = base_prop.get(key)
                            self._log(f"修改移植包build.prop键值 [{key}]:[{value}]")
                            port_prop.set(key, value)
        return True


__all__ = ["MtkSystemPortMixin"]
