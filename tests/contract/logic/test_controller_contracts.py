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

sys.path.insert(0, ".")

import json
import os
import tempfile
from pathlib import Path

from src.logic.editor.controller import EditorController
from src.platform.settings_repository import SettingsRepository
from src.app.settings.tab_controller import SettingsTabController
from src.app.tools.disable_avb_controller import DisableAvbController
from src.app.tools.disable_encryption_controller import DisableEncryptionController
from src.app.tools.get_file_info_controller import GetFileInfoController
from src.app.tools.magisk_patch_controller import MagiskPatchController
from src.logic.tools.magisk_patch.service import build_output_path


def _exercise_pure_controllers() -> None:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "a.bin"
        p.write_bytes(b"abc")
        c = GetFileInfoController(gettype_func=lambda x: "img")
        info = c.read_info(str(p))
        assert info is not None
        assert info.name == "a.bin"
        assert info.file_type == "img"
        assert info.size_bytes == 3

    class Settings:
        def __init__(self):
            self.path = "/tmp/work"
            self.error_helper_enabled = "1"
            self.error_helper_confidence = "80"
            self.magisk_not_decompress = "0"
            self.boot_skip_ramdisk = "0"
            self.treff = "0"
            self.auto_unpack = "1"
            self.contextpatch = "0"
            self.check_upgrade = "1"

        def set_value(self, k, v):
            setattr(self, k, v)

    settings = Settings()
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "x").write_text("1")
        lang_dir = Path(d) / "languages"
        lang_dir.mkdir(parents=True, exist_ok=True)
        (lang_dir / "English.json").write_text("{}", encoding="utf-8")
        ctl = SettingsTabController(
            settings_obj=settings,
            temp_path=d,
            list_languages=lambda: ("English",),
        )
        assert ctl.get_work_path() == "/tmp/work"
        assert ctl.get_cache_size() >= 1
        assert ctl.list_available_languages() == ("English",)
        ctl.set_setting("error_helper_enabled", "0")
        assert settings.error_helper_enabled == "0"
        rollback_value, rollback_enabled = ctl.handle_context_patch_toggle(
            desired_value="1", confirm_enable=lambda: False
        )
        assert (
            rollback_value == "0"
            and rollback_enabled is False
            and settings.contextpatch == "0"
        )
        accepted_value, accepted_enabled = ctl.handle_context_patch_toggle(
            desired_value="1", confirm_enable=lambda: True
        )
        assert (
            accepted_value == "1"
            and accepted_enabled is True
            and settings.contextpatch == "1"
        )
        assert ctl.clear_cache() == 0

    ru = json.loads((Path("languages") / "Russian.json").read_text(encoding="utf-8"))
    from src.ui.tabs.tools import keys as tool_keys
    from src.ui.tabs.tools.toolbox import _TOOL_SPECS

    required_language_keys = [
        "welcome_text",
        "cache_size",
        "context_patch",
        "auto_check_updates",
        "settings_models_boot_skip_decompression_hint",
        "skip_ramdisk",
        "settings_models_transparency_effect",
        "auto_unpack",
        tool_keys.TITLE,
        *(key for key, _opener_id in _TOOL_SPECS),
    ]
    for key in required_language_keys:
        assert ru.get(key)

    with tempfile.TemporaryDirectory() as d:
        boot_path = Path(d) / "boot.img"
        apk_path = Path(d) / "magisk.apk"
        boot_path.write_bytes(b"boot")
        apk_path.write_bytes(b"apk")

        class Runner:
            def __init__(self):
                self.calls = []

            def run(self, *args, **kwargs):
                self.calls.append((args, kwargs))

        runner = Runner()
        settings_repository = SettingsRepository(
            set_ini=str(Path(d) / "settings.ini"),
            load=False,
        )
        m = MagiskPatchController(
            cwd_path=d,
            temp_path=d,
            settings_obj=settings_repository,
            v_code_func=lambda: "XYZ",
            re_folder_func=lambda p: os.makedirs(p, exist_ok=True),
            task_runner=runner,
        )
        assert m.validate(
            boot_file_path=str(boot_path), magisk_apk_path=str(apk_path)
        ) == (True, None)
        m.start(
            boot_file_path=str(boot_path),
            magisk_apk_path=str(apk_path),
            is_64bit=True,
            keep_verity=False,
            keep_force_encrypt=False,
            recovery_mode=False,
            arch="arm64-v8a",
            on_success=lambda _result: None,
            on_error=lambda _error: None,
        )
        req = runner.calls[0][0][1]
        assert req.boot_file_path == str(boot_path)
        assert req.magisk_apk_path == str(apk_path)
        assert req.local_path.endswith("XYZ")
        assert req.arch == "arm64-v8a"
        assert build_output_path(
            d,
            "boot.img",
            exists_func=lambda _path: False,
            unique_suffix_func=lambda: "XYZ",
        ).endswith("boot_magisk_patched.img")

    class PM:
        def __init__(self, p):
            self.p = p

        def exist(self):
            return True

        def current_work_path(self):
            return self.p

    class JE:
        def __init__(self, p):
            self.p = p

        def read(self):
            return {"system": "ext"}

    with tempfile.TemporaryDirectory() as d:
        os.makedirs(Path(d) / "system", exist_ok=True)
        (Path(d) / "system" / "fstab.qcom").write_text("test")
        runner = type("Runner", (), {"run": lambda self, *args, **kwargs: None})()
        avb = DisableAvbController(
            project_manager=PM(d), json_edit_cls=JE, task_runner=runner
        )
        partitions = avb.scan()
        assert partitions and partitions[0].name == "system"
        assert partitions[0].paths
        enc = DisableEncryptionController(
            project_manager=PM(d), json_edit_cls=JE, task_runner=runner
        )
        partitions2 = enc.scan()
        assert partitions2 and partitions2[0].name == "system"
        assert partitions2[0].paths

    with tempfile.TemporaryDirectory() as d:
        ec = EditorController()
        ec.create_empty_file(os.path.join(d, "n.txt"))
        ec.write_file(os.path.join(d, "n.txt"), "hello")
        read_result = ec.read_file(os.path.join(d, "n.txt"), "utf-8")
        assert read_result.succeeded and read_result.content == "hello"
        assert "n.txt" in ec.list_entries(d)


def run_all() -> None:
    _exercise_pure_controllers()


def test_contracts() -> None:
    run_all()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
