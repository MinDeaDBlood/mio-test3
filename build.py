#!/usr/bin/env python3
# pylint: disable=line-too-long
# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from platform import system
from typing import List, Optional
from pathlib import Path

from pip._internal.cli.main import main as _main


RELEASE_TARGETS = {"win", "ubuntu24.04", "macos15"}
PYINSTALLER_PATHS = [".", "src", "src/core"]
PYINSTALLER_HIDDEN_IMPORTS = [
    "tkinter",
    "PIL",
    "PIL._tkinter_finder",
    "requests",
    "zstandard",
    "protobuf",
]
PYINSTALLER_EXCLUDES = ["numpy"]
ICON_PATH = Path("icon.ico")


def struct_calc_bits() -> int:
    import struct

    return struct.calcsize("P") * 8


def normalize_target_os(ostype: str, target_os: Optional[str]) -> Optional[str]:
    if target_os is None:
        if ostype == "Windows":
            raise ValueError("Windows builds require --target-os win")
        return None

    normalized = target_os.lower()
    if normalized not in RELEASE_TARGETS:
        raise ValueError(f"Unsupported --target-os: {target_os}")

    expected_platform = {
        "win": "Windows",
        "ubuntu24.04": "Linux",
        "macos15": "Darwin",
    }[normalized]
    if ostype != expected_platform:
        raise ValueError(
            f"Target {normalized} requires {expected_platform}, current platform is {ostype}"
        )
    return normalized


def resolve_artifact_name(
    ostype: str,
    machine: Optional[str] = None,
    bits: Optional[int] = None,
    target_os: Optional[str] = None,
) -> str:
    machine_name = (machine or platform.machine()).lower()
    normalized = normalize_target_os(ostype, target_os)

    if ostype == "Windows":
        arch_bits = bits or struct_calc_bits()
        if arch_bits != 64:
            raise ValueError("The Windows release target supports only 64-bit builds")
        return "MIO-KITCHEN-win.x64.zip"

    if ostype == "Linux":
        if normalized == "ubuntu24.04":
            if machine_name not in {"x86_64", "amd64"}:
                raise ValueError("The Ubuntu 24.04 release target requires x86_64")
            return "MIO-KITCHEN-ubuntu24.04-x64.zip"
        if "aarch64" in machine_name or "arm64" in machine_name:
            return "MIO-KITCHEN-linux.arm64.zip"
        if "loongarch64" in machine_name:
            return "MIO-KITCHEN-linux.loongarch64.zip"
        return "MIO-KITCHEN-linux.x64.zip"

    if ostype == "Darwin":
        if normalized == "macos15":
            if machine_name in {"x86_64", "amd64"}:
                return "MIO-KITCHEN-macos15-intel-x64.zip"
            if machine_name in {"arm64", "aarch64"}:
                return "MIO-KITCHEN-macos15-arm64.zip"
            raise ValueError(f"Unsupported macOS 15 architecture: {machine_name}")
        if machine_name in {"x86_64", "amd64"}:
            return "MIO-KITCHEN-macos.x64.zip"
        return "MIO-KITCHEN-macos.arm64.zip"

    raise ValueError(f"Unsupported platform: {ostype}")


def build_source_data_args(source_root: str = "src") -> List[str]:
    data_args: List[str] = []
    if not os.path.isdir(source_root):
        return data_args
    for root, _, files in os.walk(source_root):
        for file_name in files:
            if not file_name.endswith(".py"):
                continue
            file_path = os.path.join(root, file_name)
            data_args.extend(
                ["--add-data", f"{os.path.abspath(file_path)}{os.pathsep}{root}"]
            )
    return data_args


def _splash_path(ostype: str, machine_name: str) -> Optional[str]:
    splash_name = (
        "splash_loongarch.png"
        if ostype == "Linux" and machine_name == "loongarch64"
        else "splash.png"
    )
    splash_path = Path(splash_name)
    if splash_path.exists():
        return str(splash_path.resolve())
    return None


def build_pyinstaller_args(ostype: str, machine: Optional[str] = None) -> List[str]:
    machine_name = machine or platform.machine()
    bundle_mode = ["--onedir", "--windowed"] if ostype == "Darwin" else [
        "--onefile",
        "--windowed",
    ]
    args = [
        "tool.py",
        *bundle_mode,
        "--specpath",
        "build",
        "--collect-data",
        "sv_ttk",
        "--collect-data",
        "chlorophyll",
        "--collect-submodules",
        "src",
    ]
    for path in PYINSTALLER_PATHS:
        args.extend(["--paths", path])
    for hidden_import in PYINSTALLER_HIDDEN_IMPORTS:
        args.extend(["--hidden-import", hidden_import])
    for excluded_module in PYINSTALLER_EXCLUDES:
        args.extend(["--exclude-module", excluded_module])
    if ICON_PATH.exists():
        args.extend(["--icon", str(ICON_PATH.resolve())])

    # PyInstaller splash screens are unsupported on macOS. Windows and Linux
    # keep the existing splash behavior, including the LoongArch image.
    if ostype != "Darwin":
        splash_path = _splash_path(ostype, machine_name)
        if splash_path:
            args.extend(["--splash", splash_path])

    args.extend(build_source_data_args("src"))
    return args


class Builder:
    def __init__(
        self,
        target_os: Optional[str] = None,
        *,
        skip_install: bool = False,
        requirements_file: str = "requirements.txt",
    ):
        ostype = system()
        # Определяем архитектуру
        machine = platform.machine().lower()
        bits = struct_calc_bits()
        self.target_os = normalize_target_os(ostype, target_os)
        name = resolve_artifact_name(ostype, machine, bits, self.target_os)

        self.name = name
        self.local = os.getcwd()
        self.ostype = ostype
        self.dndplat = None
        self.skip_install = skip_install
        self.requirements_file = requirements_file

    def build(self):
        print("Building...")
        if self.skip_install:
            print("Skipping dependency installation; using prepared environment.")
        else:
            self.install_package()
        self.pyinstaller_build()
        self.config_folder()
        self.pack_zip(f"{self.local}/dist", self.name)

    def run_command(self, command: List[str], strip: bool = False):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip() if strip else result.stdout
        except subprocess.CalledProcessError:
            return None

    def generate_release_body(self):
        print("Generating Release Body...")
        # load config
        with open("config/settings.ini", "r", encoding="utf-8") as f:
            ver = [line for line in f.readlines() if "version" in line]
            ver = ver[0].strip().split(" = ")[1]
        with open("body.md", "w", encoding="utf-8", newline="\n") as f:
            f.write(f"Build times: {os.getenv('GITHUB_RUN_NUMBER')}\n")
            f.write(f"Actor: {os.getenv('GITHUB_TRIGGERING_ACTOR')}\n")
            f.write(f"Repository: {os.getenv('GITHUB_REPOSITORY')}\n")
            f.write(f"Version: {ver}\n")
            f.write("Changelog:\n")
            f.write("```\n")
            head = self.run_command(["git", "rev-parse", "HEAD"], strip=True)
            f.write(self.run_command(["git", "log", "-1", "--pretty=%B", head]))
            f.write("```\n")

    def move_artifacts(self):
        artifacts = [
            "MIO-KITCHEN-win.x64",
            "MIO-KITCHEN-ubuntu24.04-x64",
            "MIO-KITCHEN-macos15-intel-x64",
            "MIO-KITCHEN-macos15-arm64",
        ]

        for artifact in artifacts:
            source = Path(artifact) / f"{artifact}.zip"
            destination = Path(f"{artifact}.zip")
            if source.is_file():
                source.replace(destination)


    def install_package(self):
        with open(self.requirements_file, "r", encoding="utf-8") as requirements_stream:
            for requirement in requirements_stream.read().split("\n"):
                if not requirement.strip() or requirement.strip().startswith("#"):
                    continue
                print(f"Installing {requirement}")
                _main(["install", requirement])

    def pyinstaller_build(self):
        import PyInstaller.__main__

        dndplat = self.dndplat

        if os.name == "nt":
            # Windows - используем tool.spec
            mach_ = platform.machine()
            platform.machine = (
                lambda: "x86"
                if platform.architecture()[0] == "32bit" and mach_ == "AMD64"
                else mach_
            )
            if platform.machine() == "x86":
                dndplat = "win-x86"
            elif platform.machine() == "AMD64":
                dndplat = "win-x64"
            elif platform.machine() == "ARM64":
                dndplat = "win-arm64"

            # Используем tool.spec для лучшего контроля
            PyInstaller.__main__.run(
                build_pyinstaller_args("Windows", platform.machine())
            )

        elif self.ostype == "Darwin":
            if platform.machine() == "x86_64":
                dndplat = "osx-x64"
            elif platform.machine() == "arm64":
                dndplat = "osx-arm64"
            PyInstaller.__main__.run(
                build_pyinstaller_args("Darwin", platform.machine())
            )
        elif os.name == "posix":
            if self.ostype == "Linux":
                if platform.machine() == "x86_64":
                    dndplat = "linux-x64"
                elif platform.machine() == "aarch64":
                    dndplat = "linux-arm64"
                elif platform.machine() == "loongarch64":
                    dndplat = "linux-loongarch64"
            PyInstaller.__main__.run(
                build_pyinstaller_args(self.ostype, platform.machine())
            )

        self.dndplat = dndplat

    def config_folder(self):
        if not os.path.exists("dist/bin"):
            os.makedirs("dist/bin", exist_ok=True)
        while_list = [
            "images",
            "licenses",
            "extra_flash",
            self.ostype,
            "kemiaojiang.png",
            "License_kemiaojiang.txt",
            "tkdnd",
            "exec.sh",
            "Android",
            "Darwin",
            "Linux",
            "Windows",
            "keys",
            "update-binary",
        ]
        for i in os.listdir(self.local + "/bin"):
            if i in while_list:
                if os.path.isdir(f"{self.local}/bin/{i}"):
                    shutil.copytree(
                        f"{self.local}/bin/{i}",
                        f"{self.local}/dist/bin/{i}",
                        dirs_exist_ok=True,
                    )
                else:
                    shutil.copy(f"{self.local}/bin/{i}", f"{self.local}/dist/bin/{i}")
        for resource_dir in ("config", "languages", "templates"):
            source = f"{self.local}/{resource_dir}"
            destination = f"{self.local}/dist/{resource_dir}"
            if os.path.isdir(source):
                shutil.copytree(source, destination, dirs_exist_ok=True)
        plugin_db_source = f"{self.local}/plugins/plugin_db.json"
        plugin_db_destination = f"{self.local}/dist/plugins/plugin_db.json"
        os.makedirs(os.path.dirname(plugin_db_destination), exist_ok=True)
        shutil.copy(plugin_db_source, plugin_db_destination)
        for runtime_dir in (
            "plugins/installed",
            "temp/plugins/downloads",
            "temp/plugins/runtime",
            "temp/mtk_port",
            "temp/updates",
            "temp/magisk",
            "logs",
        ):
            os.makedirs(f"{self.local}/dist/{runtime_dir}", exist_ok=True)
        if os.path.exists(f"{self.local}/LICENSE") and not os.path.exists(
            "dist/LICENSE"
        ):
            shutil.copy(f"{self.local}/LICENSE", f"{self.local}/dist/LICENSE")
        elif not os.path.exists(f"{self.local}/LICENSE"):
            print("LICENSE file not found; skipping license copy.")
        # Keep all tkdnd platforms for universal build
        # if self.dndplat:
        #     for i in os.listdir(f"{self.local}/dist/bin/tkdnd"):
        #         if i[:3] == self.dndplat[:3] and i.endswith("x64") and self.dndplat.endswith('x86'):
        #             continue
        #         if i == self.dndplat:
        #             continue
        #         if os.path.isdir(f"{self.local}/dist/bin/tkdnd/{i}"):
        #             shutil.rmtree(f'{self.local}/dist/bin/tkdnd/{i}', ignore_errors=True)
        # else:
        #     raise FileNotFoundError("Cannot Build!!!TkinterDnd2 Missing!!!!!!!!!!")
        if not self.dndplat:
            raise FileNotFoundError("Cannot Build!!!TkinterDnd2 Missing!!!!!!!!!!")
        if os.name == "posix":
            if platform.machine() == "x86_64" and os.path.exists(
                f"{self.local}/dist/bin/Linux/aarch64"
            ):
                try:
                    shutil.rmtree(f"{self.local}/dist/bin/Linux/aarch64")
                except Exception as e:
                    print(e)
            for root, dirs, files in os.walk(f"{self.local}/dist", topdown=True):
                for i in files:
                    print(f"Chmod {os.path.join(root, i)}")
                    os.chmod(os.path.join(root, i), 0o7777, follow_symlinks=False)

    def pack_zip(self, source, name):
        abs_folder_path = os.path.abspath(source)
        zip_file_path = os.path.join(self.local, name)

        if self.ostype == "Darwin":
            # Preserve the .app bundle layout, symlinks, permissions, and macOS
            # metadata. Python's zipfile module does not reliably preserve all
            # of those details for an onedir application bundle.
            subprocess.run(
                [
                    "/usr/bin/ditto",
                    "-c",
                    "-k",
                    "--sequesterRsrc",
                    ".",
                    zip_file_path,
                ],
                cwd=abs_folder_path,
                check=True,
            )
            print("Pack Zip Done!")
            return

        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for root, _, files in os.walk(abs_folder_path):
                for file in files:
                    if file == name:
                        continue
                    file_path = os.path.join(root, file)
                    if ".git" in file_path:
                        continue
                    print(f"Adding: {file_path}")
                    archive.write(
                        file_path, os.path.relpath(file_path, abs_folder_path)
                    )
        print("Pack Zip Done!")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and package MIO-KITCHEN release artifacts."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="build",
        choices=("build", "grb", "ma"),
        help="build: build binary and zip; grb: generate release body; ma: move artifacts",
    )
    parser.add_argument(
        "--target-os",
        default=os.getenv("MIO_BUILD_TARGET_OS"),
        choices=("win", "ubuntu24.04", "macos15"),
        help="Release target label. Windows builds require win.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation inside build.py; useful for CI jobs with prepared environments.",
    )
    parser.add_argument(
        "--requirements-file",
        default="requirements.txt",
        help="Dependency file to install when --skip-install is not used.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    if args.command == "build":
        Builder(
            target_os=args.target_os,
            skip_install=args.skip_install,
            requirements_file=args.requirements_file,
        ).build()
    elif args.command == "grb":
        Builder(target_os=args.target_os).generate_release_body()
    elif args.command == "ma":
        Builder(target_os=args.target_os).move_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
