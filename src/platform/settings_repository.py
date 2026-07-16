from __future__ import annotations

import logging
import os
import platform
from configparser import ConfigParser

from src.platform.runtime_paths import SETTINGS_FILE
from src.core.paths import prog_path


class SettingsRepository:
    """INI backed application settings repository.

    This class owns persistence only. Applying a theme, loading localization,
    changing Tk variables and rendering appearance are UI responsibilities.
    Application controllers coordinate folder selection, persistence and restart.
    """

    def __init__(self, set_ini: str | None = None, load: bool = True):
        self.auto_unpack = "0"
        self.treff = "0"
        self.set_file = set_ini or str(SETTINGS_FILE)
        self.plugin_repo = None
        self.contextpatch = "0"
        self.oobe = "0"
        self.path = None
        self.barlevel = "0.90"
        self.error_helper_enabled = "0"
        self.error_helper_confidence = "80"
        self.version = "basic"
        self.check_upgrade = "0"
        self.version_old = "unknown"
        self.language = "English"
        self.boot_skip_ramdisk = "0"
        self.magisk_not_decompress = "0"
        self.updating = ""
        self.new_tool = ""
        self.wait_pids = ""
        self.update_files = ""
        self.update_done = "false"
        self.cmd_exit = "0"
        self.cmd_invisible = "0"
        self.debug_mode = "No"
        self.theme = "dark"
        self.alpha = "1.0"
        self.active_code = "None"
        self.update_url = "https://api.github.com/repos/ColdWindScholar/MIO-KITCHEN-SOURCE/releases/latest"
        self.config = ConfigParser()
        if os.path.isfile(self.set_file):
            if load:
                self.load()
        elif load:
            raise FileNotFoundError("settings_file_missing")
        else:
            logging.warning("settings_file_missing_bootstrap_only: %s", self.set_file)
        self.tool_bin = (
            os.path.join(prog_path, "bin", platform.system(), platform.machine())
            + os.sep
        )

    def load(self) -> None:
        self.config.read(self.set_file, encoding="utf-8")
        if not self.config.has_section("setting"):
            raise ValueError("settings_section_missing")
        for key, value in self.config.items("setting"):
            setattr(self, key, value)
        if not self.config.has_option("setting", "barlevel") and hasattr(
            self, "bar_level"
        ):
            self.barlevel = str(self.bar_level)
        self.treff = "1" if str(self.treff).strip() == "1" else "0"
        if not self.path or not os.path.isdir(self.path):
            self.path = prog_path

    def set_value(self, name: str, value: object) -> None:
        self.config.read(self.set_file, encoding="utf-8")
        if not self.config.has_section("setting"):
            raise ValueError("settings_section_missing")
        text_value = str(value)
        self.config.set("setting", name, text_value)
        with open(self.set_file, "w", encoding="utf-8", newline="\n") as file_handle:
            self.config.write(file_handle)
        setattr(self, name, text_value)


__all__ = ["SettingsRepository"]
