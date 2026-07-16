from __future__ import annotations

import os.path as op
from os import name as osname, stat, symlink, unlink, walk
from pathlib import Path
from shutil import rmtree

from src.core.mtk_port.files import UpdaterScript, compress_zip
from src.core.ota_dat import img2sdat
from src.logic.tools.mtk_port_tool.constants import TOOL_AUTHOR, TOOL_VERSION
from src.logic.tools.mtk_port_tool.operation_base import MtkPortOperationError

if osname == "nt":
    from ctypes import windll, wintypes


class MtkPackagingMixin:
    def _pack_rom(self) -> None:
        for item, item_flag in self.items["flags"].items():
            if not item_flag:
                continue
            if item == "use_custom_update-binary":
                self._log("使用提供的update-binary以解决在twrp刷入报错的问题")
                Path("tmp/rom/META-INF/com/google/android/update-binary").write_bytes(
                    self.update_binary_path.read_bytes()
                )
            elif item == "generate_script":
                self._log("自动重新生成刷机脚本解决一些莫名奇妙的问题...")
                if (not self.sdat) or self.items["partitions"]:
                    updater = Path("tmp/rom/META-INF/com/google/android/updater-script")
                    if updater.exists():
                        with updater.open(
                            "r+", encoding="utf-8", newline="\n"
                        ) as stream:
                            author = self.items.get("author") or TOOL_AUTHOR
                            version = self.items.get("version") or TOOL_VERSION
                            new_script = UpdaterScript(stream).generate(
                                author, version, self.items["partitions"]
                            )
                            if new_script:
                                stream.seek(0)
                                stream.truncate()
                                stream.write(new_script)
                                self._log("Script Generated Successfully...")
                            else:
                                self._log("Script Generated Failed...")
                    else:
                        self._log("Flash Script Not Found...")
                else:
                    self._log(
                        "刷机包可能是sdat格式或者你的partitions里没指定system和boot"
                    )
        self._log("Packing to sdcard flash rom.....", end="")
        output_path = Path(f"out/{op.basename(self.portzip)}")
        if output_path.exists():
            output_path.unlink()

        if self.sdat:
            self._pack_sdat_payload()
        compress_zip(str(output_path), "tmp/rom/")
        self._log("Done！")

    def _pack_sdat_payload(self) -> None:
        self._log("Packing to sdat...")
        self._log("Generating system image...")
        config_dir = Path("tmp/rom/config")
        contexts_path = config_dir / "system_file_contexts"
        with contexts_path.open("r+") as stream:
            unique_lines = list(
                dict.fromkeys(line.rstrip() for line in iter(stream.readline, ""))
            )
            stream.seek(0)
            stream.truncate(0)
            stream.write("\n".join(unique_lines))

        fs_labels = [["/", "0", "0", "0755"], ["/lost\\+found", "0", "0", "0700"]]
        self._append_missing_fs_labels(fs_labels)
        fs_config_path = config_dir / "system_fs_config"
        with fs_config_path.open("w", newline="\n") as stream:
            for item in sorted(fs_labels):
                stream.write(" ".join(item) + "\n")

        fit_size = self._pack_fit_size()
        system_size = stat(self.sysimg).st_size
        self.execv(
            [
                self.binaries.make_ext4fs,
                "-s",
                "-J",
                "-T",
                "1",
                "-l",
                str(system_size if system_size >= fit_size else fit_size),
                "-C",
                str(fs_config_path),
                "-S",
                str(contexts_path),
                "-L",
                "system",
                "-a",
                "system",
                "out/system_raw.img",
                "tmp/rom/system",
            ],
            verbose=True,
        )
        self.execv([self.binaries.img2simg, "out/system_raw.img", "out/system.img"])
        for path in ("tmp/rom/system", "tmp/rom/config"):
            if op.isdir(path):
                rmtree(path)
        if op.isfile("tmp/rom/system.transfer.list"):
            unlink("tmp/rom/system.transfer.list")
        img2sdat("out/system.img", "tmp/rom", self.sdat_ver)
        if op.isfile("tmp/rom/system.img"):
            self._log("Removes useless system image...")
            unlink("tmp/rom/system.img")

    def _append_missing_fs_labels(self, fs_labels: list[list[str]]) -> None:
        known = {item[0] for item in fs_labels}
        for root, dirs, files in walk("tmp/rom/system"):
            if "tmp/install" in root.replace("\\", "/"):
                continue
            for directory in dirs:
                unix_path = op.join(
                    "/system", op.relpath(op.join(root, directory), "tmp/rom/system")
                ).replace("\\", "/")
                unix_path = unix_path.replace("[", "\\[")
                if unix_path not in known:
                    fs_labels.append([unix_path.lstrip("/"), "0", "0", "0755"])
                    known.add(unix_path)
            for file_name in files:
                unix_path = op.join(
                    "/system", op.relpath(op.join(root, file_name), "tmp/rom/system")
                ).replace("\\", "/")
                unix_path = unix_path.replace("[", "\\[")
                if unix_path in known:
                    continue
                link = self._readlink(op.join(root, file_name))
                if link:
                    fs_labels.append([unix_path.lstrip("/"), "0", "2000", "0755", link])
                else:
                    mode = "0755" if "bin/" in unix_path else "0644"
                    fs_labels.append([unix_path.lstrip("/"), "0", "2000", mode])
                known.add(unix_path)

    def _pack_img(self) -> None:
        def create_symlink(source: str, destination: str) -> None:
            self._log(f"Create symlink [{source}] -> [{destination}]")
            target = Path(destination)
            target.parent.mkdir(parents=True, exist_ok=True)
            if osname == "nt":
                with open(destination, "wb") as stream:
                    stream.write(b"!<symlink>" + source.encode("utf-16") + b"\0\0")
                windll.kernel32.SetFileAttributesA(
                    destination.encode("gb2312"), wintypes.DWORD(0x4)
                )
            else:
                symlink(source, destination)

        self._log("Output will be packed as system image")
        updater = Path("tmp/rom/META-INF/com/google/android/updater-script")
        config_dir = Path("tmp/config")
        if config_dir.exists():
            rmtree(config_dir)
        config_dir.mkdir(parents=True)
        fs_labels = [["/", "0", "0", "0755"], ["/lost\\+found", "0", "0", "0700"]]
        context_labels = [
            ["/", "u:object_r:system_file:s0"],
            ["/system(/.*)?", "u:object_r:system_file:s0"],
        ]
        if not updater.exists():
            raise MtkPortOperationError(f"Flash script not found: {updater}")

        self._log("Parsing flash script...")
        last_path = ""
        for command, *args in UpdaterScript(
            updater.open("r", encoding="utf-8")
        ).content:
            if command == "symlink":
                source, *targets = args
                for target in targets:
                    create_symlink(
                        source, str(Path("tmp/rom").joinpath(target.lstrip("/")))
                    )
                continue
            if command not in {"set_metadata", "set_metadata_recursive"}:
                continue
            file_path, *metadata = args
            file_path = (
                file_path.replace("+", "\\+").replace("[", "\\[").replace("//", "/")
            )
            if file_path == last_path:
                continue
            uid, gid, mode, extra = "0", "0", "644", ""
            selinux_label = "u:object_r:system_file:s0"
            for index, token in enumerate(metadata):
                if token == "uid":
                    uid = metadata[index + 1]
                elif token == "gid":
                    gid = metadata[index + 1]
                elif token in {"mode", "fmode", "dmode"}:
                    mode = metadata[index + 1]
                elif token == "capabilities":
                    extra = (
                        ""
                        if metadata[index + 1] == "0x0"
                        else "capabilities=" + metadata[index + 1]
                    )
                elif token == "selabel":
                    selinux_label = metadata[index + 1]
            fs_labels.append([file_path.lstrip("/"), uid, gid, mode, extra])
            context_labels.append([file_path, selinux_label])
            last_path = file_path

        self._log("Add lost fs config and selinux context")
        self._append_missing_fs_labels(fs_labels)
        self._write_metadata_files(config_dir, fs_labels, context_labels)
        fit_size = self._pack_fit_size()
        system_size = stat(self.sysimg).st_size
        self.execv(
            [
                self.binaries.make_ext4fs,
                "-J",
                "-T",
                "1",
                "-l",
                str(system_size if system_size >= fit_size else fit_size),
                "-C",
                str(config_dir / "system_fs_config"),
                "-S",
                str(config_dir / "system_file_contexts"),
                "-L",
                "system",
                "-a",
                "system",
                "out/system.img",
                "tmp/rom/system",
            ],
            verbose=True,
        )
        Path("out/boot.img").write_bytes(Path("tmp/rom/boot.img").read_bytes())
        self._log(
            "Packed！\noutput boot is [out/boot.img]\noutput system is [out/system.img]"
        )

    @staticmethod
    def _write_metadata_files(
        config_dir: Path, fs_labels: list[list[str]], context_labels: list[list[str]]
    ) -> None:
        with (config_dir / "system_fs_config").open("w", newline="\n") as fs_stream:
            for item in sorted(fs_labels):
                fs_stream.write(" ".join(item) + "\n")
        with (config_dir / "system_file_contexts").open(
            "w", newline="\n"
        ) as context_stream:
            for item in sorted(context_labels):
                context_stream.write(" ".join(item) + "\n")


__all__ = ["MtkPackagingMixin"]
