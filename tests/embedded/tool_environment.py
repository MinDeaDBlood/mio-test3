
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

# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under theGNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
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
import os
import os.path
import platform
import sys
import unittest

from src.core.config_parser import ConfigParser
from src.core.random_utils import v_code

PROJECT_ROOT = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
prog_path = PROJECT_ROOT
tool_bin = (
    os.path.join(PROJECT_ROOT, "bin", platform.system(), platform.machine()) + os.sep
)
set_file = os.path.join(PROJECT_ROOT, "config", "settings.ini")


class Test(unittest.TestCase):
    def setUp(self):
        print("\nStarting Test.")

    def test_import(self):
        modules = (
            "tkinter",
            "tool",
            "src.app.entrypoint",
            "src.platform.settings_repository",
            "src.core.paths",
            "src.logic.projects.unpack.registry",
        )
        if prog_path not in sys.path:
            sys.path.append(prog_path)
        for module_name in modules:
            print(f"Importing {module_name}")
            __import__(module_name)

    def test_binaries(self):
        file_list = [
            "brotli",
            "busybox",
            "dtc",
            "e2fsdroid",
            "extract.erofs",
            "extract.f2fs",
            "imgkit",
            "img2simg",
            "lpmake",
            "magiskboot",
            "make_ext4fs",
            "mke2fs",
            "mkfs.erofs",
            "mkfs.f2fs",
            "sload.f2fs",
            "zstd",
        ]
        if platform.machine() != "x86_64" or platform.system() != "Linux":
            file_list.remove("mkfs.f2fs")
            file_list.remove("extract.f2fs")
        if os.name == "nt":
            file_list = [i + ".exe" for i in file_list]
            file_list.append("cygwin1.dll")
            file_list.append("mv.exe")
        for i in file_list:
            if not os.path.exists(os.path.join(tool_bin, i)):
                raise FileNotFoundError(f"{i} is missing!")

    def test_values_files(self):
        self.assertNotEqual(v_code(), v_code())
        self.assertIs(os.path.exists(set_file), True, "Settings File Not Found!")
        self.assertIs(os.access(set_file, os.F_OK), True, "Settings File IS Not Ok!")
        config = ConfigParser()
        config.read(set_file)
        self.assertIsNot(
            config.items("setting"), (None, None), "The Setting Config Format Is Wrong!"
        )

    def tearDown(self):
        print("Test Done!")


if __name__ == "__main__":
    unittest.main()
else:
    test_main = unittest.main
